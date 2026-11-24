# Seattle Permitting as History
{short summary - name all tools, languages, and libraries - explicitly state results}

Tool-driven project: Aim to use MS SQL, SQLAlchemy, and the ArcGIS suite in the production of an interactible webmap to demonstrate competence.



{live deployment}

{links to latest downloadable release}

## Introduction or Summary
put the project into english

address:
- why was this necessary? (problem, study question, etc.) (this content can discuss history)
- High-level outline of project
- summarize methods: what is the logic - not the history - that carried me from the study question or problem to my results
- what were the results? Is this outcome desirable?

## Libraries/Modules (if applicable) (Exchange with or fold-into Setup section)
List modules and libraries used, for purposes of reproduction/review.

Provide links for unusual libraries.

Python module requirements are handily listed in ```requirements.txt```. From the repo's root directory, set up the virtual environment with:
```shell
python -m venv .venv
# (Varies by system) Run the created 'activate' binary
pip install -r requirements.txt
```

## Data
### [Seattle Census Tracts - City of Seattle](https://data-seattlecitygis.opendata.arcgis.com/datasets/SeattleCityGIS::2020-census-tracts-seattle/about)

Census tracts (comprised of census blocks) within the City of Seattle. Some blocks along the southern boundary of the city have been left off.

|Name|Description|
|-|-|
|GEOID20|The ID assigned to this 2020 census tract|
|GROSS_ACRES<sup>1</sup>|Total coverage of census tract area|
|LAND_ACRES|Land coverage|
|WATER_ACRES|Water coverage|
|GEN_ALIAS|The name of the Community Reporting Area the tract belongs to|
|DETL_NAMES<sup>2</sup>|The names of other neighborhoods this tract is a part of|

1. The name of the field GROSS_ACRES suggests a sum of LAND_ACRES and WATER_ACRES, but I found this is never the case. GROSS_ACRES matches my own calculations within 400 sqft (see: eval_acre_figs() in tract_data_script.py), and LAND_ACRES is likewise extremely close to GROSS_ACRES when there is no water coverage. I couldn't find any documentation of this discrepency, so I have made do with the assumptions that some aspect of methodology may consider a unit of area as both land and water, and that the waterline used to calculate land may be different than that for water.
2. As designated in their associated Community Reporting Areas

I dissolve boundaries between polygons in this dataset to produce a dataset of CRA polygons (see Methodology for details). The derived dataset shares all fields with its parent except "DETL_NAMES", and the three coverage figures are calculated by the sum of the figures of their constituent tracts.

### [CPI - Bureau of Labor Statistics](https://download.bls.gov/pub/time.series/cu/)

Downloadable from their website (```cu.data.1.AllItems```). I use it to create a table of the number of Jan, 2026 dollars equivalent to 1 dollar for the given month and year.

#### Relevant fields:

|Name|Description|
|-|-|
|series_id<sup>1</sup>|the id of the data series|
|year||
|period|month (1-12)|
|value<sup>2</sup>|calculated CPI|

1. Many series are present in this dataset. I chose specifically the series ```CUSR0000SA0``` (urban, seasonally-adjusted, monthly, nationwide, all items) because it is closest to what the BLS prescribes for monthly national figures.
2. No data was collected during October '25 and part of Nov '25 - no CPI was reported for that October. I use an interpolation of adjacent months as a stand-in.

### Inflation Figures (```inflation.csv```)
Monthly ratio of dollars to January, 2026 dollars from 2005 to the end of 2025. I calculate these figures from the CPI values described above.

|Name|Description|
|-|-|
|month_id|a unique integer for a month in time|
|year||
|month|month (1-12)|
|factor|USD equivalent to Jan, 2026 dollars for that month and year|

### [Permits: City of Seattle](https://data.seattle.gov/d/76t5-zqzr)
Data for all available digital permits maintained by the Seattle Department of Construction and Inspections and available through Seattle's Open Data Portal. Updated daily.

Seattle didn't digitize all permits on record when the database launched. 2005 is the first complete year of collection.

#### Relevant fields:

|Name|Description|
|-|-|
|PermitNum<sup>1</sup>|Permit ID used by SDCI|
|PermitClassMapped|Either "residential" or "non-residential"|
|PermitTypeMapped|Another organizational category|
|Description<sup>2</sup>|Summary of expected work|
|HousingUnits<sup>3</sup>|Net change in "unit" count|
|HousingUnitsRemoved|Units added|
|HousingUnitsAdded|Units removed|
|EstProjectCost|An estimation in USD|
|IssuedDate|The date SDCI issued this permit|
|CompletedDate|Date of final passed inspection|
|StatusCurrent|The most recent step in the permitting process|
|ParentPermitNum|Overarching permit under which this one lies|

1. PermitNum is implied to be unique per entry. I found that this holds, at minimum with the filtered dataset.
2. Despite there being a StatusCurrent value for closed permits, many permits were marked "Complete" despite the Description beginning with the phrase "closed as incomplete".
3. Housing "Units" are intended to refer to entire structures, yet many permit applicants clearly treat it as "apartment units". There are many such entries left uncorrected by the SDCI.

The remaining fields are included as a measure to increase the data available for users to browse.

## `project_pemit_db` - Database Structure
4 tables: `census_tracts`, `reporting_areas`, `inflation_factors`, and `seattle_permits`.

I define the Python-side schema for each of the tables by instantiating the sqlalchemy module's `Table` class. Each table is defined for a selection of the fields I want to capture from the source data, as well I include additional columns for data transformations that will happen further down the line.

These are largely parallel with the dataset listed in the previous Data section, with some exceptions.

Sizes of string-type columns, the `N` in `varchar(N)`, were determined from the maximum string lengths of the source fields using the `survey_data()` function in my `common.py` module. For example, the longest community reporting area name is 37 characters long, so the `gen_alias` column is of type `varchar(37)`.

### Table: `census_tracts`

Officially-designated census tracts for the 2020 census.

|Field|Type|Notes|
|-|-|-|
|geoid20|bigint|*unique*|
|gross_acres<sup>1</sup>|float||
|land_acres<sup>1</sup>|float||
|water_acres<sup>1</sup>|float||
|gen_alias|varchar(37)|name of surrounding community reporting area|
|detl_names|varchar(114)|alternative neighborhood names|
|geometry|geometry|type: multipolygon|

1. I determined that water/land figures were not complementary to one another (certain areas may be considered both land *and* water), and rarely did they sum to the `gross_acres` total.

### Table: `reporting_areas`

Community reporting areas derived by Seattle city staff from census tracts.

|Field|Type|Notes|
|-|-|-|
|geoid20|bigint|*unique*; simply the first constituent tract id in sequence|
|gross_acres<sup>1, 2</sup>|float||
|land_acres<sup>1, 2</sup>|float||
|water_acres<sup>1, 2</sup>|float||
|gen_alias|varchar(37)|name|
|geometry|geometry|type: multipolygon|

1. The same caveat for use holds as with the previous table.
2. These figures are the simple sums of the area's constituent census tract.

I form this table by dissolving polygons from `census_tracts` that share a `gen_alias` value. This was accomplished using the following SQL query, which I translated to SQLAlchemy's Core functions:

```SQL
--Populate entire table with result of spatial union
INSERT INTO reporting_areas
    (gen_alias, geoid20, gross_acres, land_acres, water_acres, geometry)
SELECT gen_alias,
       MIN(geoid20),
       SUM(gross_acres),
       SUM(land_acres),
       SUM(water_acres),
       geometry::UnionAggregate(geometry)
FROM census_tracts
```

### Table: `inflation_factors`

Each row is a particular month and year. Their corresponding "factors" can be used to calculate the amount of Jan, 2026 dollars for every 1 dollar during that month and year.

|Field|Type|Notes|
|-|-|-|
|month_id|int|*unique*; simply the 6-digit year-month combo|
|year|int||
|month|int||
|factor|float||

### Table: `seattle_permits`

|Field|Type|Notes|
|-|-|-|
|permitnum|bigint|*unique*|
|permitclass|float||
|permittypedesc|float||
|description|float||
|housingunits<sup>1</sup>|smallint|net change|
|housingunitsremoved<sup>1</sup>|smallint||
|housingunitsadded<sup>1</sup>|smallint||
|estprojectcost|float|nominal dollars|
|adjestcost*|float|inflation-adjusted|
|applieddate|date||
|issueddate|date||
|expiresdate|date||
|completeddate|date||
|statuscurrent|varchar(21)||
|originaladdress|varchar(32)||
|originalzip|int||
|contractorcompanyname|varchar(44)||
|link|varchar(80)||
|zoning|varchar(25)||
|dwellingunittype|varchar(87)||
|housingcategory|varchar(23)||
|geometry|geometry|type: point|
|outside*|bit|`TRUE` if the permit location is outside all census tracts|
|tractid*|bigint|geoid20 of the surrounding (or nearest) tract|
|craid*|bigint|id of surrounding (or nearest) reporting area|

*Calculated post-hoc

1. As reported elsewhere, "Units" is intended to refer to actual buildings and not individual rentable units, bedrooms, etc. This convention is occasionally ignored by permits within the dataset.

#### Populating column `adjestcost`:

Calculating the inflation-adjusted cost-estimates for each permit involved the following parts:
1. Form a month id value for each permit, using the date within `issueddate`.
2. Use that id to look up the correct `factor` value in the table `inflation_factors`.
3. Update the permit's `adjestcost` with the product of that permit's `estprojectcost` and the `factor` value found in (2).

That logic is reflected in the following SQL query:
```SQL
--Set the adjusted cost to the product of the estimate and the factor for the month the permit was issued
UPDATE seattle_permits
SET adjestcost = estprojectcost * inflation_factors.factor
WHERE CONCAT(YEAR(issueddate), FORMAT(MONTH(issueddate), '00')) = inflation_factors.month_id
```
Likewise, I translated this query into its SQLAlchemy Core equivalent.

#### Populating column `tractid` and `outside`:

This task was accomplished in two stages:
1. Attach the `geoid20` of the tract the permit point falls within.
    - set `outside` to `TRUE` if the `tractid` remains `NULL`
2. For `NULL` ids, attach the `geoid20` of the *nearest* tract instead.

The following three queries accomplish this:
```SQL
--Attach surrounding tract id to permit
UPDATE seattle_permits
SET tractid = (
    SELECT TOP 1 census_tracts.geoid20
    FROM census_tracts
    WHERE census_tracts.geometry.STContains(seattle_permits.geometry) = 1
)
```
```SQL
--Set outside to TRUE for permits that don't fall within any tract
UPDATE seattle_permits
SET outside = CASE WHEN tractid IS NULL THEN ! ELSE 0
```
```SQL
--To permits with no tractid, attach id of nearest tract
UPDATE seattle_permits
SET tractid = (
    SELECT TOP 1 census_tracts.geoid20
    FROM census_tracts
    ORDER BY seattle_permits.geometry.STDistance(census_tracts.geometry) ASC
)
WHERE tractid IS NULL
```
The code used to build SQLAlchemy equivalents is found in `processing_scripts.py`.

#### Populating column `craid`:
Setting each permit's reporting area id was a simple matter.

Query used to model SQLAlchemy code:
```SQL
--Attach the cra id of cra's that share a gen_alias with the tract carrying the permit's tractid
UPDATE seattle_permits
SET craid = (
    SELECT TOP 1 reporting_areas.geoid20
    FROM census_tracts, reporting_areas
    WHERE seattle_permits.tractid = census_tracts.geoid20 AND census_tracts.gen_alias = reporting_areas.gen_alias
)
```

## {Methods/Methodology (name/explain each step)}
### Broad Script Design
#### SQLAlchemy: Core vs. ORM Model
A series of self-authored Python 3 scripts collect data, transfer it between project directories and database, and perform the data transformations. In service of the latter two items, I make heavy use of the SQLAlchemy module. Of the two styles of access available within that module - "Core" and "Object Relational Mapper" (or *ORM*) - I opted for the somewhat lower-level *Core* model.

Core is better suited for both the expected analysis and the demonstrative aims of this project (beyond typically-stated advantages of breadth of control) ofr the following reasons:

- Fine-grain control: I require access to functionality that bypasses ORM for Core functions anyway, often for enforcing type parity between Python dataframes and MS SQL tables.
- Dialect support: ORM does not natively support functionality unique to T-SQL. The infrastructure required is simpler/cheaper when accomplished through Core.
- Proximity to SQL: Core's functionality heavily mirrors SQL and in a couple heavily-used functions, I execute raw SQL strings.
### Seattle Municipal Census Tracts
I wanted to provide spatially-aggregated figures (e.g. "average permits per year in the Ballard neighborhood"), which meant choosing between a few spatial granularities: census blocks, census tracts (comprised of census blocks), and community reporting areas or "CRA" (which handily align to census tracts).

I prioritized accessibility for the layman and chose the community reporting area representation, so I could refer to spatial regions by their English neighborhood names. While that was the primary level of division, I also wanted to offer a more granular look at the figures. So I elected to begin with the census tract dataset and use that to produce an additional set of polygons representing CRAs.

Census tracts were loaded to the database, unchanged, in the `census_tracts` table.

I performed a spatial union within the database for tracts with the same community reporting area name (field `gen_alias`) using the SQL function `geometry::UnionAggregate`. Each tract's area figures were summed to their parent CRA. I put the results of the union into the `reporting_areas` table.

#### SQL: Geometry vs. Geography
SQL supports two different data types for representing spatial data. *Geometry* treats data as flat, as if occurring on a 2D plane, while *Geography* treats data as existing on a curved ellipsoid. The choice is mostly arbitrary because the projections of my datasets can slot into either type without reprojection and the operations I'm performing on the data are unaffected by assumed curvature.

I opted for Geometry to represent my data database-side simply for an assumed speed advantage.

### Inflation Data
I wanted to express the costs associated with the permits in current-time dollars, which allows for more meaningful trend analyses.

The Bureau of Labor Statistics publishes consumer price index figures (*CPI*)  - weighted sums of various products' prices ("*baskets*") that offer a snapshot of the United States' dollar's value and thereby a citizen's purchasing power. While the BLS publishes time series of many differently-weighted baskets, the one they consider best suited for monthly, general trends in purchasing power falls under the id ```CUSR0000SA0```.

The script ```bls_data_script.py``` downloads the BLS file containing all series through a simple GET request, and extracts the desired series by id, cutting data off outside the study window (2005 to 2025, end-of). Since CPI was not calculated for October, 2025, I used a geometric interpolation between September and November of that year as an imperfect stand-in. It then takes the ratio of each month-year's CPI to the CPI of Jan, 2026.

The transformed data is uploaded to the ```permit_project_db``` database in the `inflation_factors` table.

In effect, this table maps flattened month-year ids to multipliers. Adjusting estimated costs to today's dollars, for example, is simply a matter of multiplying the factor attached to the month and year of the permit.

### Permit Data
The focus of this project, I wanted to translate this data to a form with greater relation to the tangible reality of the city. Ideally, each entry refers to one master permit for a completed construction project, the project itself representing a discrete, physical transformation of Seattle, anchored to a single point in time when the reported or estimated changes become meaningful. (Master permits have the added virtue of consistent validity in regards to cost estimation, date, status, and changes in housing units.)

A permit is first timestamped when the application is submitted, with future timestamps for issuance, expiry, and completion. I chose the date the permit was issued to represent the permit as a "point in time", since the earliest construction for a project can legally begin is when the permit is issued. Only when construction begins, do material/labor costs start being paid, are housing units removed or added, etc.

I ignored projects were marked as complete, but contained "closed as incomplete" within the description.

The script ```sodp_data_script.py``` accesses Seattle permit data using the SODA V3 API. It submits POST request containing a query that restricts captured permits to the following criteria:
- PermitClassMapped is "Residential"
- PermitTypeMapped is "Building"
- IssuedDate is between 2005 and the end of 2025
- CurrentStatus does not indicate the permit wasn't issued, or closed prior to completion - being permissible, any of "approved to occupy", "completed", "inspections completed", "issued", and "phase issued".
- Description did not contain the phrase "closed as incomplete"
- Both HousingUnitsAdded and HousingUnitsRemoved were neither blank nor non-zero
- ParentPermitNum was blank (ensuring each entry is a master permit; avoids double-counting)
- Has location data in some form (coordinates or address)

The data is requested in csv form (requesting geojson provides no geometry).

Seven rows are missing location data but provide addresses, which the SDCI warns of. I manually pair these with lat/long coordinate pairs from a simple Google Maps search.

#### Aside:
> Seattle's Open Data Portal uses the Socrata Querying Language to interpret queries (documented [here](https://dev.socrata.com/docs/functions/#,)). I found the list of functions to be non-exhaustive; examining the urls submitted by the platform's web UI revealed additional functions available for my use, notably the two caseless functions ```caseless_starts_with``` and ```caseless_one_of```.

I added the field "AdjEstCost" for the estimated costs, adjusted for inflation, expressed in Jan, 2026 dollars. The factor of inflation drawn from BLS historical CPI data.
```SQL
SELECT
inflation_factors.factor * seattle_permits.estprojectcost as adj_cost
FROM seattle_permits
LEFT JOIN inflation_factors	ON CONCAT(YEAR(applieddate), FORMAT(MONTH(applieddate), '00')) = inflation_factors.month_id
```

Created field "Status" holding my own status categorization for each permit:
- Permits with a blank completion date and their date of expiry had lapsed received "Expired - Open"
- Otherwise, the permit's status was assigned "Active" unless the original StatusCurrent field was explicitly "Completed"


Address removing "expired" or "marked incomplete" permits, which may have had some work completed anyway.

Put these in somewhere:
- endpoint: ```'https://data.seattle.gov/api/v3/views/76t5-zqzr/query'```
- query:
```'SELECT * WHERE caseless_one_of(permitclassmapped, "residential") AND caseless_one_of(permittypemapped, "building") AND issueddate BETWEEN "2005-01-01T00:00:00" and "2025-12-31T23:59:59" AND caseless_one_of(statuscurrent, "approved to occupy", "completed", "inspections completed", "issued", "phase issued") AND NOT caseless_starts_with(description, "closed as incomplete") AND (housingunitsremoved IS NOT NULL OR housingunitsadded IS NOT NULL) AND NOT (housingunitsremoved == 0 AND housingunitsadded == 0) AND parentpermitnum IS NULL'```

{explain how it produces desirable results}

{explain what it produced}

broad outline:
- census tracts
    - find data link
    - limited dissolve by "gen_alias" [VERIFY]
    - write python script to download, cache, and load into sql "tracts_table"
- api to python script
    - save csv locally (cache)
    - create geometry column with Shape dtype from Location1 object
    - load data into sql "permits_table"
    - perform analyses 
        - estimated cost to Jan, 2026 dollars
        - logic for new "status" field
        - group by year, agg by sum
            - perform for est cost, cost-per-net-change, net-change
        - analysis by tract by year:
            - est cost, cost-per-net-change, net-change
    - export to GeoJSON
- web map site
    - finish site
    - use generated GeoJSONs from script for map layers
    - use figures generated from script for explanations
- ArcGIS Pro
    - connect to sql server
    
### {method subsection (if more than one)}
{id logic that points to this method as necessary (or just explain choice)}

{explain how it produces desirable results}

{explain what it produced}

## {Conclusions (if appropriate)}
{state the concrete conclusions of this project and how reliable/accurate/certain they are}

{explain what they mean - what is actionable? what are the implications? does this align with common perceptions? (for last q: provide links to articles if possible)}

{what further study questions arise?}

## {Findings/Results (if applicable)}
{showcase what this project produced, in contrast to any "problem" examples you provided in the intro}

{show off tricky edgecases}

{honestly portray shortcomings and list ideas for further refinement}

## {Acknowledgments/Copyrights/Links?}
{if anything I used has homepages/download pages, link them here (not programming languages)}

{think about providing copyright lol}

## {References (if made)}
{title as link}

{otherwise, citation}