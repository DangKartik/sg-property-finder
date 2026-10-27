"""Application dependency wiring."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.adapter.data_gov_sg_adapter import DataGovSgAdapter
from app.adapter.one_map_api_adapter import OneMapApiAdapter
from app.config import Settings
from app.container.report_store import ReportStore
from app.container.subzone_registry import SubzoneRegistry
from app.container.town_mapping import TownMapping
from app.control.amenity_retrieval_control import AmenityRetrievalControl
from app.control.commute_control import CommuteControl
from app.control.comparison_control import ComparisonControl
from app.control.data_availability_notifier import DataAvailabilityNotifier
from app.control.environment_retrieval_control import EnvironmentRetrievalControl
from app.control.house_pricing_retrieval_control import HousePricingRetrievalControl
from app.control.input_validation_control import InputValidationControl
from app.control.map_control import MapControl
from app.control.neighborhood_details_control import NeighborhoodDetailsControl
from app.control.ranking_control import RankingControl
from app.control.report_control import ReportControl
from app.entity.subzone_indicators import SubzoneIndicators
from app.services.dataset_service import DatasetService
from app.services.live_environment import LiveEnvironmentProvider
from app.strategy.weighted_scoring_strategy import WeightedScoringStrategy


@dataclass
class AppContext:
    """Application services shared by REST handlers."""

    settings: Settings
    dataDir: Path
    registry: SubzoneRegistry
    oneMapAdapter: Any
    dataGovAdapter: DataGovSgAdapter
    datasetService: DatasetService
    notifier: DataAvailabilityNotifier
    validator: InputValidationControl
    pricingControl: HousePricingRetrievalControl
    amenityControl: AmenityRetrievalControl
    environmentControl: EnvironmentRetrievalControl
    commuteControl: CommuteControl
    scoringStrategy: WeightedScoringStrategy
    rankingControl: RankingControl
    detailsControl: NeighborhoodDetailsControl
    comparisonControl: ComparisonControl
    mapControl: MapControl
    reportControl: ReportControl
    reportStore: ReportStore
    dataSnapshotId: str
    dataAsOf: datetime


def buildContext(
    settings: Settings | None = None,
    dataDir: Path | str | None = None,
    oneMapAdapter: Any | None = None,
) -> AppContext:
    """Wire the backend services from configuration and data assets."""
    settings = settings or Settings.fromEnv()
    base_dir = Path(dataDir) if dataDir else Path(__file__).resolve().parents[1] / "assets" / "data"
    base_dir.mkdir(parents=True, exist_ok=True)

    town_mapping_path = base_dir / "planning_area_to_hdb_town.json"
    town_mapping = TownMapping.fromFile(town_mapping_path) if town_mapping_path.exists() else TownMapping({})

    data_gov = DataGovSgAdapter(
        settings.DATA_GOV_SG_BASE_URL,
        settings.DATA_GOV_SG_API_KEY,
        realtimeBaseUrl=settings.DATA_GOV_SG_REALTIME_BASE_URL,
        fallbackDir=base_dir,
    )
    dataset_service = DatasetService(
        data_gov,
        base_dir,
        maxAgeHours=settings.DATA_MAX_AGE_HOURS,
    )
    try:
        subzone_payload = dataset_service.getSubzones()
        registry = SubzoneRegistry.fromGeoJsonPayload(subzone_payload, town_mapping)
    except Exception:
        registry = SubzoneRegistry()
    notifier = DataAvailabilityNotifier()
    if oneMapAdapter is None:
        oneMapAdapter = OneMapApiAdapter(
            settings.ONEMAP_BASE_URL,
            settings.ONEMAP_EMAIL or "",
            settings.ONEMAP_PASSWORD or "",
        )

    pricing = HousePricingRetrievalControl(
        data_gov,
        notifier,
        dataPath=base_dir / "hdb_resale.csv",
        subzoneRegistry=registry,
        datasetService=dataset_service,
    )
    amenities = AmenityRetrievalControl(
        data_gov,
        notifier,
        amenitiesPath=base_dir / "amenities.json",
        subzoneRegistry=registry,
    )
    live_environment = LiveEnvironmentProvider(data_gov)
    environment = EnvironmentRetrievalControl(
        data_gov,
        notifier,
        baselinePath=base_dir / "environment_baselines.json",
        liveProvider=(
            live_environment.get if settings.APP_ENV.lower() != "test" else None
        ),
        subzoneRegistry=registry,
    )
    _enrichRegistry(registry, amenities, environment, pricing, base_dir)

    commute = CommuteControl(
        oneMapAdapter,
        notifier,
        matrixPath=base_dir / "commute_matrix.json",
    )
    for code in commute.insufficientDataSubzoneCodes:
        try:
            registry.getSubzone(code).dataAvailable = False
        except KeyError:
            continue
    scoring = WeightedScoringStrategy()
    dataset_status = dataset_service.status()
    subzone_status = dataset_status.get("subzones") or {}
    data_snapshot = subzone_status.get("dataSnapshotId", "LOCAL")
    data_as_of = subzone_status.get("dataAsOf", datetime.now(timezone.utc))
    ranking = RankingControl(
        registry,
        scoring,
        commute,
        notifier,
        dataSnapshotId=data_snapshot,
        dataAsOf=data_as_of,
    )
    details = NeighborhoodDetailsControl(
        amenities,
        environment,
        pricing,
        commute,
        registry,
    )
    comparison = ComparisonControl(ranking, details)
    store = ReportStore()
    report = ReportControl(notifier, store)
    map_control = MapControl(registry, oneMapAdapter, commute)
    return AppContext(
        settings=settings,
        dataDir=base_dir,
        registry=registry,
        oneMapAdapter=oneMapAdapter,
        dataGovAdapter=data_gov,
        datasetService=dataset_service,
        notifier=notifier,
        validator=InputValidationControl(oneMapAdapter),
        pricingControl=pricing,
        amenityControl=amenities,
        environmentControl=environment,
        commuteControl=commute,
        scoringStrategy=scoring,
        rankingControl=ranking,
        detailsControl=details,
        comparisonControl=comparison,
        mapControl=map_control,
        reportControl=report,
        reportStore=store,
        dataSnapshotId=data_snapshot,
        dataAsOf=data_as_of,
    )


def _enrichRegistry(
    registry: SubzoneRegistry,
    amenities: AmenityRetrievalControl,
    environment: EnvironmentRetrievalControl,
    pricing: HousePricingRetrievalControl,
    dataDir: Path,
) -> None:
    """Attach derived indicators to every subzone when local assets exist."""
    has_amenities = (dataDir / "amenities.json").exists()
    has_environment = (dataDir / "environment_baselines.json").exists()
    has_pricing = (dataDir / "hdb_resale.csv").exists() or (dataDir / "hdb_resale.json").exists()
    if not any((has_amenities, has_environment, has_pricing)):
        return

    pricing_by_town: dict[str, dict] = {}
    if has_pricing:
        representative_by_town: dict[str, str] = {}
        for subzone in registry.getAllSubzones():
            representative_by_town.setdefault(subzone.townName, subzone.subzoneCode)
        for town, subzone_code in representative_by_town.items():
            try:
                pricing_by_town[town] = pricing.retrieveHousePricing(subzone_code).data
            except Exception:
                pricing_by_town[town] = {}

    for subzone in registry.getAllSubzones():
        indicators = SubzoneIndicators()
        try:
            if has_amenities:
                indicators = amenities.retrieveIndicators(subzone.subzoneCode).data
            if has_environment:
                env_indicators = environment.retrieveIndicators(
                    subzone.subzoneCode, includeLive=False
                ).data
                indicators.greenCoveragePercent500m = env_indicators.greenCoveragePercent500m
                indicators.pm25Baseline = env_indicators.pm25Baseline
                indicators.dataAsOf = env_indicators.dataAsOf
            if has_pricing:
                pricing_result = pricing_by_town.get(subzone.townName, {})
                if pricing_result:
                    medians = {
                        flat_type: (entry.getMedianPrice() or entry.averagePrice)
                        for flat_type, entry in pricing_result.items()
                    }
                    indicators.medianPriceByFlatType = medians
                    indicators.transactionCountByFlatType = {
                        flat_type: entry.transactionCount
                        for flat_type, entry in pricing_result.items()
                    }
                    indicators.medianResalePrice = statistics.median(medians.values())
                    indicators.medianPricePerSqm = statistics.median(
                        entry.medianPricePerSqm for entry in pricing_result.values()
                    )
                    indicators.transactionCount12m = sum(
                        entry.transactionCount for entry in pricing_result.values()
                    )
                    indicators.priceTrendPercent = statistics.fmean(
                        entry.priceTrendPercent for entry in pricing_result.values()
                    )
            subzone.indicators = indicators
        except Exception:
            subzone.indicators = indicators
