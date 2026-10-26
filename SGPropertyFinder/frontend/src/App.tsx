import { useCallback, useEffect, useMemo, useState } from "react";
import L from "leaflet";
import { api, requireData } from "./api/client";
import { ProfileCatalog } from "./container/ProfileCatalog";
import { ProfileControl } from "./control/ProfileControl";
import { ComparisonUI } from "./boundary/ComparisonUI";
import { ExportReportUI } from "./boundary/ExportReportUI";
import { FactSheetUI } from "./boundary/FactSheetUI";
import { NeighborhoodMapUI } from "./boundary/NeighborhoodMapUI";
import { NotificationModalUI } from "./boundary/NotificationModalUI";
import { ProfileFormUI } from "./boundary/ProfileFormUI";
import { ProfileSelectorUI } from "./boundary/ProfileSelectorUI";
import { ResultsListUI } from "./boundary/ResultsListUI";
import type {
  AmenityPointDTO,
  CoordinatesDTO,
  CriterionDefinitionDTO,
  DataStatusMapDTO,
  MapDataDTO,
  ProfileDTO,
  RecommendationSetDTO,
  RouteDataDTO,
} from "./types/dto";
import { formatDate } from "./utils/format";
import { nearbyAmenities } from "./utils/amenities";
import { unavailableSubzoneIds as listUnavailableSubzoneIds } from "./utils/subzones";

const profileCatalog = new ProfileCatalog();
const profileControl = new ProfileControl(profileCatalog, api);

interface NotificationState {
  title: string;
  message: string;
}

export default function App() {
  const [criteria, setCriteria] = useState<CriterionDefinitionDTO[]>([]);
  const [profiles, setProfiles] = useState<ProfileDTO[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<string | null>(null);
  const [editingProfile, setEditingProfile] = useState<ProfileDTO | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [recommendations, setRecommendations] = useState<RecommendationSetDTO | null>(null);
  const [mapData, setMapData] = useState<MapDataDTO | null>(null);
  const [amenities, setAmenities] = useState<AmenityPointDTO[]>([]);
  const [selectedSubzoneId, setSelectedSubzoneId] = useState<string | null>(null);
  const [sharedSubzoneIds, setSharedSubzoneIds] = useState<string[]>([]);
  const [factsheetCode, setFactsheetCode] = useState<string | null>(null);
  const [comparisonIds, setComparisonIds] = useState<string[]>([]);
  const [comparisonOpen, setComparisonOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [notification, setNotification] = useState<NotificationState | null>(null);
  const [bottomNotice, setBottomNotice] = useState<string | null>(null);
  const [route, setRoute] = useState<RouteDataDTO | null>(null);
  const [busy, setBusy] = useState(false);
  const [refreshingData, setRefreshingData] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [dataStatus, setDataStatus] = useState<DataStatusMapDTO | null>(null);

  const notify = useCallback((title: string, message: string) => {
    setNotification({ title, message });
  }, []);

  useEffect(() => {
    if (!bottomNotice) return;
    const timer = window.setTimeout(() => setBottomNotice(null), 4500);
    return () => window.clearTimeout(timer);
  }, [bottomNotice]);

  const showInsufficientDataNotice = useCallback(
    (subzoneId: string) => {
      const name = findSubzoneName(mapData, subzoneId);
      setBottomNotice(`Insufficient data for ${name}. Select another neighbourhood.`);
    },
    [mapData],
  );

  const activeProfile = useMemo(
    () => profiles.find((profile) => profile.profileId === activeProfileId) ?? null,
    [profiles, activeProfileId],
  );

  const unavailableIds = useMemo(
    () => listUnavailableSubzoneIds(mapData),
    [mapData],
  );
  const unavailableSet = useMemo(
    () => new Set(unavailableIds),
    [unavailableIds],
  );

  useEffect(() => {
    if (selectedSubzoneId && unavailableSet.has(selectedSubzoneId)) {
      setSelectedSubzoneId(null);
      setFactsheetCode(null);
    }
  }, [selectedSubzoneId, unavailableSet]);

  const visibleRecommendations = useMemo(() => {
    if (!recommendations) return null;
    const items = recommendations.items
      .filter((item) => !unavailableSet.has(item.subzoneId))
      .map((item, index) => ({ ...item, rank: index + 1 }));
    const warnings = recommendations.warnings.filter(
      (warning) =>
        warning.subzoneCode === null || !unavailableSet.has(warning.subzoneCode),
    );
    return { ...recommendations, items, warnings };
  }, [recommendations, unavailableSet]);

  const scores = useMemo(() => {
    const next: Record<string, number> = {};
    (visibleRecommendations?.items ?? []).forEach((item) => {
      next[item.subzoneId] = item.totalScore;
    });
    return next;
  }, [visibleRecommendations]);

  const routeDestination = useMemo(
    () => (mapData && selectedSubzoneId ? featureCenter(mapData, selectedSubzoneId) : null),
    [mapData, selectedSubzoneId],
  );

  const focusedAmenities = useMemo(
    () =>
      selectedSubzoneId && mapData
        ? nearbyAmenities(amenities, featureCenter(mapData, selectedSubzoneId))
        : [],
    [amenities, mapData, selectedSubzoneId],
  );

  const refreshProfiles = useCallback(async () => {
    try {
      const loaded = await profileCatalog.loadFromLocalStorage();
      setProfiles(loaded);
      return loaded;
    } catch (error) {
      notify("Cannot read local plans", error instanceof Error ? error.message : "IndexedDB is unavailable.");
      return [];
    }
  }, [notify]);

  const runRanking = useCallback(
    async (profile: ProfileDTO) => {
      setBusy(true);
      try {
        const envelope = await api.generateRankedRecommendations(profile);
        const result = requireData(envelope);
        setRecommendations(result);
        setSelectedSubzoneId(null);
        setSharedSubzoneIds([]);
        setComparisonIds([]);
        setRoute(null);
      } catch (error) {
        notify(
          "Ranking failed",
          error instanceof Error ? error.message : "The backend could not generate recommendations.",
        );
      } finally {
        setBusy(false);
      }
    },
    [notify],
  );

  const handleRefreshData = useCallback(async () => {
    setRefreshingData(true);
    try {
      const envelope = await api.refreshData();
      const statuses = requireData(envelope);
      setDataStatus(statuses);
      const amenitiesEnvelope = await api.getAmenities().catch(() => null);
      if (amenitiesEnvelope?.success && amenitiesEnvelope.data) {
        setAmenities(amenitiesEnvelope.data);
      }
      if (activeProfile) {
        await runRanking(activeProfile);
      }
      notify(
        "Data refreshed",
        "Subzone and HDB snapshots have been refreshed from data.gov.sg.",
      );
    } catch (error) {
      notify(
        "Data refresh failed",
        error instanceof Error
          ? error.message
          : "The backend could not refresh its datasets.",
      );
    } finally {
      setRefreshingData(false);
    }
  }, [activeProfile, notify, runRanking]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const sharePayload = new URLSearchParams(window.location.search).get("share");
        const [
          criteriaEnvelope,
          mapEnvelope,
          amenitiesEnvelope,
          statusEnvelope,
          loadedProfiles,
          shareEnvelope,
        ] = await Promise.all([
          api.getCriteria(),
          api.generateMapData(),
          api.getAmenities().catch(() => null),
          api.getStatus().catch(() => null),
          profileCatalog.loadFromLocalStorage().catch(() => [] as ProfileDTO[]),
          sharePayload
            ? api.decodeShare(sharePayload).catch(() => null)
            : Promise.resolve(null),
        ]);
        if (!mounted) return;
        setCriteria(requireData(criteriaEnvelope));
        const loadedMapData = requireData(mapEnvelope);
        setMapData(loadedMapData);
        if (amenitiesEnvelope?.success && amenitiesEnvelope.data) {
          setAmenities(amenitiesEnvelope.data);
        }
        if (statusEnvelope?.success && statusEnvelope.data) {
          setDataStatus(statusEnvelope.data);
        }
        setProfiles(loadedProfiles);

        if (shareEnvelope?.success && shareEnvelope.data) {
          const scenario = shareEnvelope.data;
          const savedProfileId = await profileCatalog.saveToLocalStorage(scenario.profile);
          const savedProfiles = await profileCatalog.loadFromLocalStorage();
          if (!mounted) return;
          const savedProfile =
            savedProfiles.find((profile) => profile.profileId === savedProfileId) ?? {
              ...scenario.profile,
              profileId: savedProfileId,
            };
          setProfiles(savedProfiles);
          setActiveProfileId(savedProfileId);
          setShowForm(false);
          setEditingProfile(null);
          await runRanking(savedProfile);
          if (!mounted) return;
          const unavailable = new Set(listUnavailableSubzoneIds(loadedMapData));
          const sharedCodes = scenario.subzoneCodes.filter(
            (code) => !unavailable.has(code),
          );
          setSharedSubzoneIds(sharedCodes);
          setComparisonIds(sharedCodes.slice(0, 4));
          setSelectedSubzoneId(sharedCodes[0] ?? null);
          const url = new URL(window.location.href);
          url.searchParams.delete("share");
          window.history.replaceState({}, "", url.toString());
          return;
        }

        if (sharePayload && (!shareEnvelope || !shareEnvelope.success)) {
          notify(
            "Invalid share link",
            shareEnvelope?.error?.message ?? "The shared scenario could not be loaded.",
          );
        }

        if (loadedProfiles.length > 0) {
          const first = loadedProfiles[0];
          setActiveProfileId(first.profileId);
          await runRanking(first);
        }
      } catch (error) {
        if (mounted) {
          notify(
            "Backend unavailable",
            error instanceof Error
              ? error.message
              : "Start FastAPI on port 8000 and refresh the page.",
          );
        }
      } finally {
        if (mounted) setInitialLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [notify, runRanking]);

  useEffect(() => {
    if (!selectedSubzoneId || !activeProfile?.anchorCoordinates || !routeDestination) {
      setRoute(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const envelope = await api.getCommuteOverlay(
          activeProfile.anchorCoordinates as CoordinatesDTO,
          routeDestination,
          activeProfile.preferredCommuteMode,
        );
        if (!cancelled) setRoute(requireData(envelope));
      } catch {
        if (!cancelled) setRoute(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [
    selectedSubzoneId,
    activeProfile?.anchorCoordinates?.latitude,
    activeProfile?.anchorCoordinates?.longitude,
    activeProfile?.preferredCommuteMode,
    routeDestination,
  ]);

  async function handleSaved(profileId: string) {
    const loaded = await refreshProfiles();
    const profile = loaded.find((item) => item.profileId === profileId);
    setActiveProfileId(profileId);
    setShowForm(false);
    setEditingProfile(null);
    if (profile) {
      await runRanking(profile);
    }
  }

  async function handleSelectProfile(profileId: string) {
    const profile = profiles.find((item) => item.profileId === profileId);
    if (!profile) return;
    setActiveProfileId(profileId);
    setShowForm(false);
    setEditingProfile(null);
    setFactsheetCode(null);
    await runRanking(profile);
  }

  async function handleDeleteProfile(profileId: string) {
    try {
      await profileControl.deleteProfile(profileId);
      const loaded = await refreshProfiles();
      if (profileId === activeProfileId) {
        const next = loaded[0] ?? null;
        setActiveProfileId(next?.profileId ?? null);
        setRecommendations(null);
        setSelectedSubzoneId(null);
        setComparisonIds([]);
        if (next) await runRanking(next);
      }
    } catch (error) {
      notify("Could not delete plan", error instanceof Error ? error.message : "Try again.");
    }
  }

  function selectSubzone(subzoneId: string) {
    if (unavailableSet.has(subzoneId)) {
      setSelectedSubzoneId(null);
      setFactsheetCode(null);
      setRoute(null);
      showInsufficientDataNotice(subzoneId);
      return;
    }
    setSelectedSubzoneId(subzoneId);
    setBottomNotice(null);
    window.setTimeout(() => {
      document
        .getElementById(`result-${subzoneId}`)
        ?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 30);
  }

  function openFactsheet(subzoneId: string) {
    if (unavailableSet.has(subzoneId)) {
      setSelectedSubzoneId(null);
      setFactsheetCode(null);
      setRoute(null);
      showInsufficientDataNotice(subzoneId);
      return;
    }
    setFactsheetCode(subzoneId);
    setBottomNotice(null);
  }

  function toggleComparison(subzoneId: string) {
    if (unavailableSet.has(subzoneId)) {
      showInsufficientDataNotice(subzoneId);
      return;
    }
    setBottomNotice(null);
    setComparisonIds((current) => {
      if (current.includes(subzoneId)) {
        return current.filter((id) => id !== subzoneId);
      }
      if (current.length >= 4) {
        notify("Comparison limit reached", "Select at most four neighbourhoods.");
        return current;
      }
      return [...current, subzoneId];
    });
  }

  function openComparison() {
    if (comparisonIds.length < 2) {
      notify("Select at least two areas", "Choose two or more neighbourhoods in the results list.");
      return;
    }
    setComparisonOpen(true);
  }

  function openExport() {
    if (!activeProfile) {
      notify("No active plan", "Create or select a preference plan before exporting.");
      return;
    }
    setExportOpen(true);
  }

  const subzoneStatus = dataStatus?.subzones;
  const sourceLabel =
    subzoneStatus?.source === "data.gov.sg:live" ? "Live data.gov.sg" : "Data.gov.sg snapshot";

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">SC2006 · Neighbourhood recommender</p>
          <h1>SG Property Finder</h1>
          <p className="header-subtitle">
            Rank neighbourhoods by affordability, commute, schools, greenery and amenities.
          </p>
        </div>
        <div className="header-actions">
          <div className={`data-pill ${subzoneStatus?.isStale ? "stale" : ""}`}>
            <span className="status-dot" />
            {sourceLabel}
            {subzoneStatus?.dataAsOf && <> · {formatDate(subzoneStatus.dataAsOf)}</>}
          </div>
          <ProfileSelectorUI
            profiles={profiles}
            activeProfileId={activeProfileId}
            busy={busy}
            onSelect={(id) => void handleSelectProfile(id)}
            onEdit={(id) => {
              const profile = profiles.find((item) => item.profileId === id) ?? null;
              setEditingProfile(profile);
              setShowForm(true);
            }}
            onDelete={(id) => void handleDeleteProfile(id)}
          />
          <button
            className="button primary"
            onClick={() => {
              setEditingProfile(null);
              setShowForm(true);
            }}
          >
            + New plan
          </button>
        </div>
      </header>

      {initialLoading ? (
        <main className="loading-screen">
          <div className="spinner" />
          <p>Loading criteria, neighbourhood geometry and saved plans…</p>
        </main>
      ) : (
        <main className="app-grid">
          <section className="map-column">
            <NeighborhoodMapUI
              mapData={mapData}
              scores={scores}
              selectedSubzoneId={selectedSubzoneId}
              highlightedSubzoneIds={sharedSubzoneIds}
              unavailableSubzoneIds={unavailableIds}
              amenities={focusedAmenities}
              route={route}
              routeOrigin={activeProfile?.anchorCoordinates ?? null}
              routeDestination={routeDestination}
              onSelect={selectSubzone}
              onRefresh={() => void handleRefreshData()}
              refreshing={refreshingData || busy}
            />
            {selectedSubzoneId && (
              <div className="map-selection-bar">
                <span>
                  Selected: <strong>{findSubzoneName(mapData, selectedSubzoneId)}</strong>
                </span>
                {unavailableSet.has(selectedSubzoneId) ? (
                  <span className="insufficient-data-label">Insufficient data</span>
                ) : (
                  <button className="button small" onClick={() => openFactsheet(selectedSubzoneId)}>
                    Open factsheet
                  </button>
                )}
              </div>
            )}
          </section>

          <aside className="sidebar recommendations-sidebar">
            <ResultsListUI
              recommendationSet={visibleRecommendations}
              selectedSubzoneId={selectedSubzoneId}
              comparisonIds={comparisonIds}
              unavailableSubzoneIds={unavailableIds}
              loading={busy}
              onSelect={selectSubzone}
              onToggleCompare={toggleComparison}
              onOpenComparison={openComparison}
              onOpenFactsheet={openFactsheet}
              onExport={openExport}
              exportDisabled={!activeProfile}
            />
          </aside>
        </main>
      )}

      {showForm && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => {
          setShowForm(false);
          setEditingProfile(null);
        }}>
          <section
            className="modal plan-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Preference plan editor"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <ProfileFormUI
              key={editingProfile?.profileId ?? "new-profile"}
              profileControl={profileControl}
              addressSearchApi={api}
              criteria={criteria}
              initialProfile={editingProfile}
              onSaved={(id) => void handleSaved(id)}
              onCancel={() => {
                setShowForm(false);
                setEditingProfile(null);
              }}
              onNotify={notify}
            />
          </section>
        </div>
      )}

      {factsheetCode && activeProfile && (
        <FactSheetUI
          subzoneCode={factsheetCode}
          profile={activeProfile}
          detailsApi={api}
          onClose={() => setFactsheetCode(null)}
          onNotify={notify}
        />
      )}

      <ComparisonUI
        open={comparisonOpen}
        profile={activeProfile}
        subzoneCodes={comparisonIds}
        comparisonApi={api}
        onClose={() => setComparisonOpen(false)}
        onNotify={notify}
      />

      <ExportReportUI
        open={exportOpen}
        profile={activeProfile}
        recommendationSet={visibleRecommendations}
        subzoneCodes={comparisonIds}
        reportApi={api}
        onClose={() => setExportOpen(false)}
        onNotify={notify}
      />

      {bottomNotice && (
        <div className="bottom-toast" role="status" aria-live="polite">
          {bottomNotice}
        </div>
      )}

      {notification && (
        <NotificationModalUI
          title={notification.title}
          message={notification.message}
          onClose={() => setNotification(null)}
        />
      )}
    </div>
  );
}

function featureCenter(mapData: MapDataDTO, subzoneCode: string): CoordinatesDTO | null {
  const collection = mapData.geojson as {
    features?: Array<{ properties?: { subzoneCode?: string }; geometry?: unknown }>;
  };
  const feature = collection.features?.find(
    (item) => item.properties?.subzoneCode === subzoneCode,
  );
  if (!feature?.geometry) {
    return null;
  }
  try {
    // Leaflet's GeoJSON layer gives a robust bounds centre for Polygon/MultiPolygon.
    const layer = L.geoJSON(feature as never);
    const center = layer.getBounds().getCenter();
    return { latitude: center.lat, longitude: center.lng };
  } catch {
    return null;
  }
}

function findSubzoneName(mapData: MapDataDTO | null, subzoneCode: string): string {
  const collection = mapData?.geojson as {
    features?: Array<{ properties?: { subzoneCode?: string; subzoneName?: string } }>;
  };
  return (
    collection?.features?.find((item) => item.properties?.subzoneCode === subzoneCode)
      ?.properties?.subzoneName ?? subzoneCode
  );
}
