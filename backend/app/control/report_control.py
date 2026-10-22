"""PDF report generation and shareable URLs."""

from __future__ import annotations

import base64
import html
import io
import json
import shutil
import tempfile
import uuid
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from app.container.report_store import ReportStore
from app.entity.pdf_report import PdfReport
from app.strategy.criterion_catalog import buildDefaultCriterionCatalog

if TYPE_CHECKING:
    from app.control.data_availability_notifier import DataAvailabilityNotifier
    from app.entity.preference_profile import PreferenceProfile
    from app.entity.recommendation_set import RecommendationSet
    from app.schemas.neighborhood_detail_dto import NeighborhoodDetailDTO


class ReportControl:
    """Stereotype: Control. Stateless PDF report generator."""

    def __init__(
        self,
        notifier: DataAvailabilityNotifier,
        reportStore: ReportStore | None = None,
        reportDir: Path | str | None = None,
        publicBaseUrl: str = "",
    ) -> None:
        """Create the report control with a short-lived report store."""
        self.notifier = notifier
        self.reportStore = reportStore or ReportStore()
        self.reportDir = Path(reportDir) if reportDir else Path(tempfile.mkdtemp(prefix="sgpropfinder-reports-"))
        self.reportDir.mkdir(parents=True, exist_ok=True)
        self.publicBaseUrl = publicBaseUrl.rstrip("/")

    def generatePdfReport(
        self,
        recommendations: RecommendationSet,
        details: list[NeighborhoodDetailDTO],
    ) -> PdfReport:
        """Render a PDF, store it locally and return secure download metadata."""
        report_id = uuid.uuid4().hex
        generated = datetime.now(timezone.utc)
        expires = generated + timedelta(minutes=15)
        filename = f"SGPropFinder_Report_{report_id[:8]}.pdf"
        path = self.reportDir / filename
        content = self._renderReport(recommendations, details)
        path.write_bytes(content)
        self.reportStore.add(report_id, path, expires)
        return PdfReport(
            reportId=report_id,
            generatedTime=generated,
            downloadUrl=f"{self.publicBaseUrl}/api/v1/reports/download/{report_id}",
            expiresAt=expires,
            fileName=filename,
            contentType="application/pdf",
            sizeBytes=len(content),
        )

    def exportToFile(self, report: PdfReport, filePath: str) -> bool:
        """Copy a stored report to a caller-supplied path."""
        source = self.reportStore.getPath(report.reportId)
        if source is None or not source.exists():
            return False
        target = Path(filePath)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        return True

    def generateShareableUrl(
        self,
        profile: PreferenceProfile,
        subzoneCodes: list[str],
        baseUrl: str = "/",
    ) -> str:
        """Serialize profile inputs and selected subzones into a query string."""
        payload = {
            "profile": _toJsonable(profile),
            "subzones": list(subzoneCodes),
        }
        encoded = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        ).decode("ascii")
        separator = "&" if "?" in baseUrl else "?"
        return f"{baseUrl}{separator}{urlencode({'share': encoded})}"

    def _renderReport(
        self,
        recommendations: RecommendationSet,
        details: list[NeighborhoodDetailDTO],
    ) -> bytes:
        """Render the report directly with ReportLab Platypus."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        styles = getSampleStyleSheet()
        body = styles["BodyText"]
        subheading = styles["Heading3"]
        small = ParagraphStyle(
            "Small",
            parent=body,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#475467"),
        )
        header = ParagraphStyle(
            "TableHeader",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
        )
        bullet = ParagraphStyle(
            "Bullet",
            parent=body,
            leftIndent=10,
            bulletIndent=0,
            spaceAfter=3,
        )

        catalog = buildDefaultCriterionCatalog()
        labels = {
            definition.criterionId: definition.criterionName
            for definition in catalog.getAllCriteria()
        }
        snapshot = recommendations.profileSnapshot or {}
        profile_name = str(snapshot.get("profileName") or recommendations.profileId)
        flat_types = snapshot.get("selectedFlatTypes") or []
        profile_summary = " | ".join(
            [
                f"<b>Profile:</b> {html.escape(profile_name)}",
                f"<b>Budget:</b> {_formatCurrency(snapshot.get('budgetMin'))} to "
                f"{_formatCurrency(snapshot.get('budgetMax'))}",
                f"<b>Flat types:</b> "
                f"{html.escape(', '.join(str(item) for item in flat_types)) or '—'}",
                f"<b>Workplace:</b> "
                f"{html.escape(str(snapshot.get('workplaceAddress') or '—'))}",
                f"<b>Commute:</b> "
                f"{html.escape(str(snapshot.get('preferredCommuteMode') or '—'))}",
            ]
        )

        story = [
            Paragraph("Neighbourhood Recommendation Report", styles["Title"]),
            Spacer(1, 6),
            Paragraph(
                f"Generated: {_formatTimestamp(recommendations.generatedTime)} | "
                f"Snapshot: {html.escape(recommendations.dataSnapshotId)} | "
                f"Data as of: {_formatTimestamp(recommendations.dataAsOf)}",
                small,
            ),
            Spacer(1, 8),
            Paragraph(profile_summary, body),
            Spacer(1, 14),
            Paragraph("Profile and weighting", styles["Heading2"]),
        ]

        weight_rows = _weightTableRows(snapshot, labels)
        if weight_rows:
            weight_data: list[list[Paragraph]] = [
                [
                    Paragraph("Criterion", header),
                    Paragraph("Importance (1-10)", header),
                    Paragraph("Relative weight", header),
                ]
            ]
            weight_data.extend(
                [
                    [
                        Paragraph(html.escape(label), body),
                        Paragraph(importance, body),
                        Paragraph(normalised, body),
                    ]
                    for label, importance, normalised in weight_rows
                ]
            )
            weight_table = Table(weight_data, colWidths=[80 * mm, 42 * mm, 42 * mm])
            weight_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(weight_table)
        else:
            story.append(
                Paragraph(
                    "Importance ratings were not recorded in this recommendation snapshot.",
                    small,
                )
            )

        story.extend([Spacer(1, 16), Paragraph("Ranked recommendations", styles["Heading2"])])
        recommendation_rows: list[list[Paragraph]] = [
            [
                Paragraph("Rank", header),
                Paragraph("Subzone", header),
                Paragraph("Score", header),
            ]
        ]
        for item in recommendations.getItems():
            recommendation_rows.append(
                [
                    Paragraph(str(item.rank), body),
                    Paragraph(html.escape(item.subzoneName), body),
                    Paragraph(f"{item.totalScore:.1f}", body),
                ]
            )
        if len(recommendation_rows) == 1:
            recommendation_rows.append(
                [
                    Paragraph("—", body),
                    Paragraph("No recommendations", body),
                    Paragraph("—", body),
                ]
            )
        recommendation_table = Table(
            recommendation_rows,
            colWidths=[18 * mm, 112 * mm, 28 * mm],
            repeatRows=1,
        )
        recommendation_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(recommendation_table)

        story.extend(
            [Spacer(1, 16), Paragraph("Neighbourhood details", styles["Heading2"])]
        )
        detail_rows: list[list[Paragraph]] = [
            [
                Paragraph("Subzone", header),
                Paragraph("Pricing", header),
                Paragraph("Green coverage", header),
                Paragraph("Commute", header),
            ]
        ]
        for detail in details:
            prices = ", ".join(
                f"{html.escape(flat)}: "
                f"{_formatCurrency(pricing.getMedianPrice() or pricing.averagePrice)}"
                f"{' (town proxy)' if pricing.isTownProxy else ''}"
                for flat, pricing in detail.pricing.items()
            )
            detail_rows.append(
                [
                    Paragraph(html.escape(detail.subzoneName), body),
                    Paragraph(prices or "No pricing data", body),
                    Paragraph(f"{detail.environment.greenCoveragePercent:.1f}%", body),
                    Paragraph(f"{detail.commute.durationMinutes} min", body),
                ]
            )
        if len(detail_rows) == 1:
            detail_rows.append(
                [
                    Paragraph("—", body),
                    Paragraph("No details", body),
                    Paragraph("—", body),
                    Paragraph("—", body),
                ]
            )
        detail_table = Table(
            detail_rows,
            colWidths=[42 * mm, 76 * mm, 22 * mm, 18 * mm],
            repeatRows=1,
        )
        detail_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(detail_table)

        items_by_code = {item.subzoneId: item for item in recommendations.getItems()}
        story.extend(
            [Spacer(1, 16), Paragraph("Criterion scores", styles["Heading2"])]
        )
        for detail in details:
            story.append(
                Paragraph(
                    f"{html.escape(detail.subzoneName)} ({html.escape(detail.subzoneCode)})",
                    subheading,
                )
            )
            item = items_by_code.get(detail.subzoneCode)
            if item is None or not item.criterionScores:
                story.append(
                    Paragraph(
                        "Criterion score rows are unavailable because this subzone is "
                        "outside the returned top-20 ranking or has no scored criteria.",
                        small,
                    )
                )
                story.append(Spacer(1, 8))
                continue
            score_rows: list[list[Paragraph]] = [
                [
                    Paragraph("Criterion", header),
                    Paragraph("Raw", header),
                    Paragraph("Score (0-100)", header),
                    Paragraph("Weight", header),
                    Paragraph("Contribution", header),
                    Paragraph("Source", header),
                ]
            ]
            for score in item.criterionScores:
                if score.isMissing:
                    values = ["—", "—", "—", "—", "Missing"]
                else:
                    values = [
                        f"{score.rawValue:,.2f}",
                        f"{score.normalisedScore * 100:.1f}",
                        f"{score.weight * 100:.1f}%",
                        f"{score.weightedScore * 100:.1f}",
                        score.source,
                    ]
                score_rows.append(
                    [
                        Paragraph(
                            html.escape(labels.get(score.criterionId, score.criterionId)),
                            body,
                        ),
                        Paragraph(values[0], body),
                        Paragraph(values[1], body),
                        Paragraph(values[2], body),
                        Paragraph(values[3], body),
                        Paragraph(html.escape(values[4]), body),
                    ]
                )
            score_table = Table(
                score_rows,
                colWidths=[42 * mm, 20 * mm, 23 * mm, 18 * mm, 23 * mm, 48 * mm],
                repeatRows=1,
            )
            score_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.extend([score_table, Spacer(1, 8)])

        story.extend([Spacer(1, 8), Paragraph("Data dates", styles["Heading2"])])
        date_rows: list[list[Paragraph]] = [
            [
                Paragraph("Subzone", header),
                Paragraph("Factsheet generated", header),
                Paragraph("Pricing as of", header),
                Paragraph("Environment as of", header),
                Paragraph("Commute departure", header),
            ]
        ]
        for detail in details:
            pricing_dates = sorted(
                {
                    _formatTimestamp(pricing.asOf)
                    for pricing in detail.pricing.values()
                    if pricing.asOf is not None
                }
            )
            date_rows.append(
                [
                    Paragraph(html.escape(detail.subzoneName), body),
                    Paragraph(_formatTimestamp(detail.generatedTime), body),
                    Paragraph(", ".join(pricing_dates) or "—", body),
                    Paragraph(_formatTimestamp(detail.environment.asOf), body),
                    Paragraph(_formatTimestamp(detail.commute.departureTime), body),
                ]
            )
        date_table = Table(
            date_rows,
            colWidths=[38 * mm, 32 * mm, 38 * mm, 34 * mm, 32 * mm],
            repeatRows=1,
        )
        date_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(date_table)

        story.extend([Spacer(1, 16), Paragraph("Caveats", styles["Heading2"])])
        caveats = [
            "Scores combine fixed-domain criterion scores with relative weights "
            "derived from 1-10 importance ratings normalised to sum to 1.0.",
            "HDB pricing uses a 12-month rolling median. Entries marked 'town proxy' "
            "use the HDB-town median because subzone-level transactions are unavailable.",
            "Environment green-coverage and PM2.5 baselines are deterministic regional "
            "values, not a verified 10-year NParks time series. Live weather, PM2.5 "
            "and UVI are display-only.",
            "Commute estimates use OneMap. Public-transport matrix entries may use a "
            "straight-line fallback when live routing or a matrix entry is unavailable.",
            "Amenity counts use buffer-distance density from the subzone representative "
            "point, not point-in-polygon containment.",
            "Missing criteria are excluded and the remaining criterion weights are "
            "renormalised.",
        ]
        caveats.extend(
            detail.pricingNote
            for detail in details
            if detail.pricingNote
        )
        for message in list(dict.fromkeys(caveats)):
            story.append(Paragraph(f"• {html.escape(message)}", bullet))

        story.extend([Spacer(1, 12), Paragraph("Data warnings", styles["Heading2"])])
        warnings = recommendations.warnings + [
            warning for detail in details for warning in detail.warnings
        ]
        messages = list(dict.fromkeys(warning.message for warning in warnings))
        if messages:
            for message in messages:
                story.append(Paragraph(f"• {html.escape(message)}", bullet))
        else:
            story.append(Paragraph("None", body))

        story.extend(
            [
                Spacer(1, 18),
                Paragraph("Generated by SG Property Finder.", small),
            ]
        )

        buffer = io.BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            title="Neighbourhood Report",
            author="SG Property Finder",
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )
        document.build(story)
        return buffer.getvalue()


def _weightTableRows(
    snapshot: dict[str, Any],
    labels: dict[str, str],
) -> list[tuple[str, str, str]]:
    """Return (label, importance, relative weight) rows for the report."""
    entries = snapshot.get("criteriaWeights")
    if not isinstance(entries, list):
        return []
    ratings: list[tuple[str, float]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        criterion_id = str(entry.get("criterionId") or "").strip()
        value = _number(entry.get("weightValue"))
        if criterion_id and value is not None:
            ratings.append((criterion_id, value))
    total = sum(max(0.0, value) for _, value in ratings)
    if not ratings or total <= 0:
        return []
    return [
        (
            labels.get(criterion_id, criterion_id),
            f"{value:g}",
            f"{(max(0.0, value) / total) * 100:.1f}%",
        )
        for criterion_id, value in ratings
    ]


def _number(value: Any) -> float | None:
    """Convert a numeric snapshot value, returning None when invalid."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _formatCurrency(value: Any) -> str:
    """Format a SGD value for the report."""
    numeric = _number(value)
    return f"S${numeric:,.0f}" if numeric is not None else "—"


def _formatTimestamp(value: Any) -> str:
    """Format a timestamp for the report."""
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def _toJsonable(value: Any) -> Any:
    """Convert dataclasses, enums, dates and nested containers to JSON values."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return {key: _toJsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _toJsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_toJsonable(item) for item in value]
    return value
