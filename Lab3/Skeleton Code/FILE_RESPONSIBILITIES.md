# Skeleton Code — File Responsibilities

This document describes what each file in the skeleton code is responsible for, based on the class design model (Lab 3) and the project description.

The codebase follows a layered architecture:

| Package | Role |
| --- | --- |
| `boundary` | UI classes — render the interface and capture user input |
| `control` | Control classes — coordinate use cases and business logic |
| `entity` | Entity classes — domain data objects |
| `container` | Containers/registries — hold and persist collections of entities |
| `adapter` | Adapters — wrap the external APIs (data.gov.sg, OneMap) |
| `strategy` | Strategy pattern — pluggable scoring algorithm |

---

## Root

### `__init__.py`
Marks the `Skeleton Code` folder as a Python package. Intentionally empty.

### `README.md`
Project readme with repository/deliverable instructions (not part of the code itself).

---

## `adapter/`

### `__init__.py`
Marks `adapter` as a Python package. Intentionally empty.

### `data_gov_sg_adapter.py` — `DataGovSgAdapter`
Adapter for the **data.gov.sg API**. Responsible for:
- Fetching datasets (housing/resale prices, amenities, environment data) by `resourceId`.
- Keeping the API endpoint and any API-specific details private to this class (encapsulation/access control) so no other class deals with the raw API.

### `one_map_api_adapter.py` — `OneMapApiAdapter`
Adapter for the **OneMap API**. Responsible for:
- Getting routing data (`getRoutingData`) between an origin and destination for a travel mode, used for commute estimates.
- Getting basemap tiles (`getBasemapTile`) for the Leaflet map.
- Storing the `apiKey` and `baseUrl` privately — API keys never leave this class.

---

## `boundary/`

### `__init__.py`
Marks `boundary` as a Python package. Intentionally empty.

### `profile_form_ui.py` — `ProfileFormUI`
The preference input form. Responsible for:
- Rendering the form where users key in preferences (budget range, flat types, workplace address) and adjust criterion sliders.
- Submitting the entered profile data.
- Displaying validation error messages when input is invalid.

### `profile_selector_ui.py` — `ProfileSelectorUI`
The saved-profiles dropdown. Responsible for:
- Rendering the list of previously saved `PreferenceProfile`s.
- Handling selection of a profile (`onProfileSelected`).

### `results_list_ui.py` — `ResultsListUI`
The ranked recommendations list. Responsible for:
- Rendering a `RecommendationSet` as a ranked list.
- Handling clicks on a subzone to drill into its details.

### `neighborhood_map_ui.py` — `NeighborhoodMapUI`
The interactive map (Leaflet). Responsible for:
- Rendering the map of Singapore with choropleth layers for subzones.
- Highlighting a selected subzone.
- Rendering a commute overlay (e.g., route/time from the workplace to a subzone).

### `fact_sheet_ui.py` — `FactSheetUI`
The neighbourhood detail view. Responsible for:
- Displaying all details of the selected subzone: amenities, environment info, housing pricing, and commute estimate.

### `export_report_ui.py` — `ExportReportUI`
The PDF export modal. Responsible for:
- Rendering the export modal.
- Triggering PDF generation.
- Displaying the download link for the generated report.

### `notification_modal_ui.py` — `NotificationModalUI`
A generic notification modal. Responsible for:
- Showing a modal with a title and message (`showModal`).
- Closing the modal (`closeModal`).
- Used by `DataAvailabilityNotifier` to inform users when data is missing/unavailable.

---

## `container/`

### `__init__.py`
Marks `container` as a Python package. Intentionally empty.

### `profile_catalog.py` — `ProfileCatalog`
In-memory store of all saved `PreferenceProfile`s. Responsible for:
- Adding, retrieving, listing, and removing profiles.
- **Persistence**: reading/writing profiles to IndexedDB/local storage (`saveToLocalStorage`, `loadFromLocalStorage`, `deleteProfile`). Centralizing storage here means a future storage change is a single-point change.

### `subzone_registry.py` — `SubzoneRegistry`
In-memory store of all `Subzone`s. Responsible for:
- Registering, retrieving (by subzone code), and listing subzones used across ranking, mapping, and details views.

---

## `control/`

### `__init__.py`
Marks `control` as a Python package. Intentionally empty.

### `system_startup_control.py` — `SystemStartupControl`
Application entry point. Responsible for:
- Initializing the system (`initializeSystem`): loading the `ProfileCatalog` and `SubzoneRegistry`.
- Launching the UI (`launchUI`).

### `profile_control.py` — `ProfileControl`
Coordinates the create/update/delete profile use case. Responsible for:
- Creating new profiles, updating and deleting existing ones via `ProfileCatalog`.
- Delegating input checks to `InputValidationControl`.

### `input_validation_control.py` — `InputValidationControl`
Validates user-entered profile data. Responsible for:
- Checking profile form data (`validateProfileData`) and returning a `ValidationResult`.
- Enabling the system to notify users when inputs are invalid.

### `ranking_control.py` — `RankingControl`
Coordinates the recommendation ranking use case. Responsible for:
- Selecting the active profile.
- Computing the suitability score for each subzone using the pluggable `ScoringStrategy`.
- Generating a ranked `RecommendationSet` (`generateRankedRecommendations`).

### `map_control.py` — `MapControl`
Coordinates map data. Responsible for:
- Generating the list of subzones to show on the map.
- Fetching subzone boundary polygons via `OneMapApiAdapter`.

### `commute_control.py` — `CommuteControl`
Coordinates commute estimation. Responsible for:
- Retrieving a `CommuteEstimate` (duration, distance, transfers) for an origin/destination pair and travel mode via `OneMapApiAdapter`.

### `neighborhood_details_control.py` — `NeighborhoodDetailsControl`
Coordinates the "view neighbourhood details" use case. Responsible for:
- Orchestrating the amenity, environment, pricing, and commute retrieval controls.
- Assembling their results into a single neighbourhood detail DTO for the UI.

### `retrieval_control.py` — `RetrievalControl` (abstract)
**Template Method** base class for all data.gov.sg retrievals. Responsible for:
- Defining the common fetch → parse → notify-if-missing flow (`fetchData`).
- Handling missing data (`handleMissingData`) via `DataAvailabilityNotifier`.
- Subclasses override only the parsing step (`parseResponse`).

### `amenity_retrieval_control.py` — `AmenityRetrievalControl`
Extends `RetrievalControl`. Responsible for:
- Retrieving amenities (parks, schools, hospitals, malls, transport) for a subzone and returning `List<AmenityInfo>`.

### `environment_retrieval_control.py` — `EnvironmentRetrievalControl`
Extends `RetrievalControl`. Responsible for:
- Retrieving environment data (weather pattern, green coverage) for a subzone and returning `EnvironmentInfo`.

### `house_pricing_retrieval_control.py` — `HousePricingRetrievalControl`
Extends `RetrievalControl`. Responsible for:
- Retrieving housing price data (average price, median price per sqm, price trend) for a subzone and returning `HousePricing`.

### `report_control.py` — `ReportControl`
Coordinates the "export to PDF" use case. Responsible for:
- Generating a `PdfReport` from a `RecommendationSet` and neighbourhood details (showing which neighbourhood meets the user's requirements and why).
- Raising notifications (via `DataAvailabilityNotifier`) if anything needed for the report is missing.

### `data_availability_notifier.py` — `DataAvailabilityNotifier`
Responsible for:
- Notifying the user when data for a specific neighbourhood or criterion is unavailable, by showing a `NotificationModalUI`.

---

## `entity/`

### `__init__.py`
Marks `entity` as a Python package. Intentionally empty.

### `preference_profile.py` — `PreferenceProfile`
The user's preference profile. Responsible for:
- Holding profile identity, budget range, selected flat types, workplace address, anchor coordinates, creation/update timestamps, active flag, and criterion weights.
- Updating its own details and managing its `CriterionWeight`s.

### `criterion_weight.py` — `CriterionWeight`
A single preference criterion and its importance. Responsible for:
- Holding a criterion name and its weight value, with getters/setters.

### `subzone.py` — `Subzone`
A neighbourhood subzone. Responsible for:
- Holding the subzone code, name, boundary polygon, and computed suitability score, with getters/setters.

### `recommendation_set.py` — `RecommendationSet`
The output of a ranking run. Responsible for:
- Holding the profile id, generation time, and list of `RecommendationItem`s; adding items and sorting them by rank.

### `recommendation_item.py` — `RecommendationItem`
One ranked result. Responsible for:
- Holding the subzone id, rank, total score, and the per-criterion score breakdown.

### `commute_estimate.py` — `CommuteEstimate`
A commute result. Responsible for:
- Holding duration (minutes), distance (km), transfer count, and travel mode, with getters.

### `amenity_info.py` — `AmenityInfo`
A single amenity. Responsible for:
- Holding the amenity name, category, and location (coordinates).

### `house_pricing.py` — `HousePricing`
Housing price data for a subzone. Responsible for:
- Holding average price, median price per sqm, and price trend, with getters.

### `environment_info.py` — `EnvironmentInfo`
Environment data for a subzone. Responsible for:
- Holding the weather pattern and green coverage percentage, with getters.

### `pdf_report.py` — `PdfReport`
A generated PDF report. Responsible for:
- Holding the report id, generation time, and file path, with getters.

### `types.py` — Shared types
Shared helper types used across layers. Responsible for:
- Defining common data structures not modelled as full entities, e.g. `Coordinates`, `Polygon`, `ProfileDTO`, `ValidationResult`, and `NeighborhoodDetailDTO`.

---

## `strategy/`

### `__init__.py`
Marks `strategy` as a Python package. Intentionally empty.

### `scoring_strategy.py` — `ScoringStrategy`
The **Strategy** interface for scoring. Responsible for:
- Declaring `computeSuitabilityScore(subzone, profile, commute)` so `RankingControl` can score without knowing the algorithm.

### `weighted_scoring_strategy.py` — `WeightedScoringStrategy`
Concrete implementation of `ScoringStrategy`. Responsible for:
- Computing the 0–100 suitability score by applying the user's criterion weights to the subzone data (prices, amenities, commute, environment).
- The scoring algorithm can be swapped out (e.g., a different strategy) without modifying `RankingControl`.
