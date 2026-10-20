# Skeleton Code — File Responsibilities

Generated from `Lab3/Class_Diagram.drawio`. Each file holds one class from the class diagram. Attribute and method names follow the diagram exactly (camelCase), with diagram types mapped to Python types (`String`→`str`, `double`→`float`, `List<T>`→`list[T]`, `Map<K,V>`→`dict[K, V]`).

**Running / importing:** imports are rooted at this folder, so run Python from inside `Skeleton Code` (for example `python -c "import control.ranking_control"`). Method bodies are `raise NotImplementedError  # TODO` until implemented.

| Package | Role |
| --- | --- |
| `boundary` | UI classes: render the interface and capture user input |
| `control` | Control classes: coordinate use cases and business logic |
| `entity` | Entity classes: domain data objects |
| `container` | Containers/registries: hold and persist collections of entities |
| `adapter` | Adapters: wrap the external APIs (data.gov.sg, OneMap) |
| `strategy` | Strategy pattern: pluggable scoring algorithm |

Shared types the diagram uses but never defines (`Coordinates`, `ProfileForm`, `ValidationResult`, `RawResponse`, `MapData`, `RouteData`, `FactSheetData`, `TransitMode`) are declared as empty placeholder classes in `entity/types.py`.

---

## `boundary/`

### `boundary/notification_modal_ui.py` — `NotificationModalUI` («boundary»)
Shows notifications and error messages to the user in a modal.

Attributes:
- `- currentMessage: String`

Operations:
- `+ showNotification(message: String, type: String): void`
- `+ dismiss(): void`

### `boundary/profile_form_ui.py` — `ProfileFormUI` («boundary»)
Form where the user keys in a preference profile and criterion weights.

Attributes:
- `- profileControl: ProfileControl`

Operations:
- `+ renderForm(): void`
- `+ onSubmit(formData: Map<String, Object>): void`

### `boundary/profile_selector_ui.py` — `ProfileSelectorUI` («boundary»)
Dropdown of saved preference profiles; selecting one triggers ranking.

Attributes:
- `- rankingControl: RankingControl`

Operations:
- `+ renderSelector(profiles: List<PreferenceProfile>): void`
- `+ onSelectProfile(profileId: String): void`

### `boundary/results_list_ui.py` — `ResultsListUI` («boundary»)
Displays the ranked list of recommended subzones.

Attributes:
- `- rankingControl: RankingControl`

Operations:
- `+ renderResults(results: RecommendationSet): void`
- `+ onSubzoneClick(subzoneId: String): void`

### `boundary/neighborhood_map_ui.py` — `NeighborhoodMapUI` («boundary»)
Interactive map of subzones with the commute route layer.

Attributes:
- `- mapControl: MapControl`

Operations:
- `+ renderMap(subzones: List<Subzone>): void`
- `+ renderCommuteLayer(routes: List<CommuteEstimate>): void`

### `boundary/fact_sheet_ui.py` — `FactSheetUI` («boundary»)
Fact sheet with amenities, pricing, environment and commute details of one subzone.

Attributes:
- `- detailsControl: NeighborhoodDetailsControl`

Operations:
- `+ displaySubzoneDetails(subzoneId: String): void`

### `boundary/export_report_ui.py` — `ExportReportUI` («boundary»)
Export dialog used to download the recommendations as a PDF report.

Attributes:
- `- reportControl: ReportControl`

Operations:
- `+ openExportModal(): void`
- `+ onConfirmExport(format: String): void`

## `control/`

### `control/system_startup_control.py` — `SystemStartupControl` («control»)
Singleton start-up class that initialises the system on launch.

Attributes:
- `- instance: SystemStartupControl`
- `- profileCatalog: ProfileCatalog`
- `- subzoneRegistry: SubzoneRegistry`

Operations:
- `+ getInstance(): SystemStartupControl`
- `+ main(args: String[]): void`
- `+ initializeSystem(): void`

### `control/profile_control.py` — `ProfileControl` («control»)
Creates and updates preference profiles after validating the input.

Attributes:
- `- profileCatalog: ProfileCatalog`

Operations:
- `+ createProfile(profileData: ProfileForm): boolean`
- `+ updateProfile(id: String, profileData: ProfileForm): boolean`

### `control/input_validation_control.py` — `InputValidationControl` («control»)
Validates profile form input and reports errors.

Operations:
- `+ validateProfileForm(formData: Map<String, Object>): ValidationResult`

### `control/data_availability_notifier.py` — `DataAvailabilityNotifier` («control»)
Tells the user when data for a subzone or criterion is unavailable.

Operations:
- `+ notifyMissingData(source: String, entityId: String): void`

### `control/ranking_control.py` — `RankingControl` («control»)
Ranks subzones against the selected profile using a scoring strategy.

Attributes:
- `- subzoneRegistry: SubzoneRegistry`
- `- commuteControl: CommuteControl`
- `- mapAdapter: OneMapApiAdapter`

Operations:
- `+ getSubzonePolygons(): MapData`
- `+ getCommuteOverlay(start: Coordinates, dest: Coordinates): RouteData`

### `control/map_control.py` — `MapControl` («control»)
Prepares map data (subzone polygons, commute overlay) for the map UI.

Attributes:
- `- subzoneRegistry: SubzoneRegistry`
- `- commuteControl: CommuteControl`
- `- mapAdapter: OneMapApiAdapter`

Operations:
- `+ getSubzonePolygons(): MapData`
- `+ getCommuteOverlay(start: Coordinates, dest: Coordinates): RouteData`

### `control/commute_control.py` — `CommuteControl` («control»)
Calculates commute time and distance through the OneMap adapter.

Attributes:
- `- apiAdapter: OneMapApiAdapter`

Operations:
- `+ calculateTravelTime(origin: Coordinates, dest: Coordinates, mode: TransitMode): CommuteEstimate`

### `control/neighborhood_details_control.py` — `NeighborhoodDetailsControl` («control»)
Collects amenity, environment and pricing data into one fact sheet.

Attributes:
- `- amenityRetrieval: RetrievalControl`
- `- envRetrieval: RetrievalControl`
- `- priceRetrieval: RetrievalControl`

Operations:
- `+ getFullFactSheet(subzoneId: String): FactSheetData`

### `control/retrieval_control.py` — `RetrievalControl` («control», abstract)
Template-method base class for fetching and parsing data.gov.sg datasets.

Attributes:
- `# dataAdapter: DataGovSgAdapter`

Operations:
- `+ fetchData(datasetId: String): RawResponse`
- `# parseResponse(data: RawResponse): Object`

Template Method: subclasses override `parseResponse` only.

### `control/amenity_retrieval_control.py` — `AmenityRetrievalControl` («control»)
Retrieves and parses amenity data for a subzone. Extends `RetrievalControl`.

Operations:
- `# parseResponse(data: RawResponse): List<AmenityInfo>`
- `+ fetchAmenitiesForSubzone(subzoneId: String): List<AmenityInfo>`

### `control/environmental_retrieval_control.py` — `EnvironmentalRetrievalControl` («control»)
Retrieves and parses environmental data for a subzone. Extends `RetrievalControl`.

Operations:
- `# parseResponse(data: RawResponse): List<AmenityInfo>`
- `+ fetchEnvironmentForSubzone(subzoneId: String): List<AmenityInfo>`

### `control/house_pricing_retrieval_control.py` — `HousePricingRetrievalControl` («control»)
Retrieves and parses house pricing data for a subzone. Extends `RetrievalControl`.

Operations:
- `# parseResponse(data: RawResponse): List<AmenityInfo>`
- `+ fetchPricingForSubzone(subzoneId: String): List<AmenityInfo>`

### `control/report_control.py` — `ReportControl` («control»)
Generates the PDF report and exports it to a file.

Attributes:
- `- lastGeneratedReport: PdfReport`

Operations:
- `+ generatePdfReport(recommendationSet: RecommendationSet): PdfReport`
- `+ exportToFile(report: PdfReport, filePath: String): boolean`

## `container/`

### `container/profile_catalog.py` — `ProfileCatalog` («container»)
Holds all saved preference profiles and persists them in the browser's IndexedDB.

Attributes:
- `- profiles: Map<String, PreferenceProfile>`

Operations:
- `+ addProfile(profile: PreferenceProfile): void`
- `+ getProfile(id: String): PreferenceProfile`
- `+ getAllProfiles(): List<PreferenceProfile>`
- `+ deleteProfile(id: String): void`
- `+ saveToIndexedDB(): void`
- `+ loadFromIndexedDB(): void`

### `container/subzone_registry.py` — `SubzoneRegistry` («container»)
Holds all subzones loaded from the external datasets.

Attributes:
- `- subzones: Map<String, Subzone>`

Operations:
- `+ getSubzone(id: String): Subzone`
- `+ getAllSubzones(): List<Subzone>`
- `+ loadSubzones(data: List<Subzone>): void`

## `entity/`

### `entity/preference_profile.py` — `PreferenceProfile` («entity»)
A user's saved preferences and the weight given to each criterion.

Attributes:
- `- profileId: String`
- `- profileName: String`
- `- criteriaWeights: List<CriterionWeight>`

Operations:
- `+ getWeightForCriterion(criterion: String): double`
- `+ updateWeight(criterion: String, weight: double): void`

### `entity/criterion_weight.py` — `CriterionWeight` («entity»)
The importance a user assigns to one criterion.

Attributes:
- `- criterionName: String`
- `- weightValue: double`

Operations:
- `+ getCriterionName(): String`
- `+ getWeightValue(): double`

### `entity/subzone.py` — `Subzone` («entity»)
A Singapore subzone with its boundary, amenities, commute estimates, pricing and environment data.

Attributes:
- `- subzoneId: String`
- `- name: String`
- `- boundariesGeoJson: String`
- `- amenities: List<AmenityInfo>`
- `- commuteEstimates: List<CommuteEstimate>`
- `- pricing: HousePricing`
- `- environment: EnvironmentInfo`

Operations:
- `+ getId(): String`
- `+ addAmenity(amenity: AmenityInfo): void`
- `+ setHousePricing(pricing: HousePricing): void`

### `entity/amenity_info.py` — `AmenityInfo` («entity»)
One amenity (school, hospital, park, mall...) located in a subzone.

Attributes:
- `- amenityId: String`
- `- category: String`
- `- name: String`
- `- location: Coordinates`

Operations:
- `+ getCategory(): String`
- `+ getName(): String`

### `entity/house_pricing.py` — `HousePricing` («entity»)
House pricing figures for a subzone.

Attributes:
- `- medianPrice: double`
- `- propertyType: String`
- `- pricePerSqFt: double`

Operations:
- `+ getMedianPrice(): double`

### `entity/environment_info.py` — `EnvironmentInfo` («entity»)
Environmental quality figures for a subzone.

Attributes:
- `- airQualityIndex: int`
- `- greenSpacePercentage: double`
- `- averageNoiseLevelDb: double`

Operations:
- `+ getGreenSpace(): double`

### `entity/commute_estimate.py` — `CommuteEstimate` («entity»)
Estimated commute from the workplace to a subzone.

Attributes:
- `- durationMinutes: int`
- `- transitMode: String`
- `- distanceKm: double`

Operations:
- `+ getDuration(): int`
- `+ getMode(): String`

### `entity/recommendation_set.py` — `RecommendationSet` («entity»)
The set of ranked recommendations generated for a profile.

Attributes:
- `- setId: String`
- `- generatedTimestamp: Date`
- `- items: List<RecommendationItem>`

Operations:
- `+ addItem(item: RecommendationItem): void`
- `+ getSortedItems(): List<RecommendationItem>`

### `entity/recommendation_item.py` — `RecommendationItem` («entity»)
One ranked subzone with its suitability score.

Attributes:
- `- rank: int`
- `- totalScore: double`
- `- targetSubzone: Subzone`

Operations:
- `+ getRank(): int`
- `+ getScore(): double`
- `+ getSubzone(): Subzone`

### `entity/pdf_report.py` — `PdfReport` («entity»)
A generated PDF report of the recommendations.

Attributes:
- `- reportId: String`
- `- contentBytes: byte[]`
- `- createdAt: Date`

Operations:
- `+ getFileStream(): InputStream`

## `adapter/`

### `adapter/one_map_api_adapter.py` — `OneMapApiAdapter` («adapter»)
Adapter hiding the OneMap API behind a simple interface.

Attributes:
- `- baseUrl: String`

Operations:
- `+ fetchDataset(datasetId: String): String`

### `adapter/data_gov_sg_adapter.py` — `DataGovSgAdapter` («adapter»)
Adapter hiding the data.gov.sg API behind a simple interface; the API key stays private here.

Attributes:
- `- apiKey: String`
- `- baseUrl: String`

Operations:
- `+ fetchRoute(start: Coordinates, end: Coordinates): String`
- `+ fetchSubzonePolygons(): String`

## `strategy/`

### `strategy/scoring_strategy.py` — `ScoringStrategy` («strategy», interface)
Strategy interface for computing a subzone's suitability score.

Operations:
- `+ calculateScore(subzone: Subzone, profile: PreferenceProfile): double`

### `strategy/weighted_scoring_strategy.py` — `WeightedScoringStrategy` («strategy»)
Scores a subzone as a weighted sum of criterion scores. Extends `ScoringStrategy`.

Attributes:
- `- weightsMap: Map<String, Double>`

Operations:
- `+ calculateScore(subzone: Subzone, profile: PreferenceProfile): double`

## `entity/types.py`
Placeholder declarations for the shared types listed above.
