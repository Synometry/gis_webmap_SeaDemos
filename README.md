# {Project Title}
{short summary - name all tools, languages, and libraries - explicitly state results}

{live deployment}

{links to latest downloadable release}

## Introduction or Summary
put the project into english

address:
- why was this necessary? (problem, study question, etc.) (this content can discuss history)
- summarize methods: what is the logic - not the history - that carried me from the study question or problem to my results
- what were the results? Is this outcome desirable?

## Data
### [Permits: City of Seattle](https://data.seattle.gov/d/76t5-zqzr)
Data for all available digital permits maintained by the Seattle Department of Construction and Inspections and available through Seattle's Open Data Portal. Updated daily.

Seattle didn't digitize all permits on record when the database launched. 2005 is the first complete year.

Noteworthy fields:

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

1. PermitNum is implied to be unique per entry. I found that this was(n't)[VERIFY] the case.
2. Despite there being a StatusCurrent value for closed permits, many permits were marked "Complete" despite the Description beginning with the phrase "marked closed for incomplete" [VERIFYANDHOWMANY?]
3. Housing "Units" are intended to refer to entire structures, yet many permit applicants clearly treat it as "apartment units", uncorrected by the SDCI.

## {Methods/Methodology (name/explain each step)}
### Inflation Data
I queried the Version 1.0 endpoint of the Bureau of Labor Statistics API for Consumer Price Index figures.

### Permit Data
The focus of this project, I wanted to translate this data to a form with greater relation to the tangible reality of the city. The desired form is therefore that each entry refers to one master permit for a completed construction project, the project itself representing a discrete, physical transformation of Seattle, anchored to a single point in time when the reported or estimated changes become meaningful. (Master permits have the added virtue of consistent validity in regards to cost estimation, date, status, and changes in housing units.)

A permit is first timestamped when the application is submitted, with future timestamps for issuance, expiry, and completion. I chose the date the permit was issued to represent the permit as a "point in time", since the earliest construction for a project can legally begin is when the permit is issued. Only when construction begins, do material/labor costs start being paid, are housing units removed or added, etc.

Some projects were marked as complete, but contained "marked closed as incomplete" [VERIFY]

I accessed Seattle permit data on [DATE], using the online querying tool to immediately select only the permits matching the following criteria:
- PermitClassMapped = "Residential"
- PermitTypeMapped = "Building"
- IssuedDate between 2005 and 2026
- CurrentStatus does not indicate the permit was rejected, didn't happen, expired, etc.
- Description did not contain the phrase "[POPULATE]"
- HousingUnitsAdded and HousingUnitsRemoved were neither blank nor non-zero
- ParentPermitNum was blank (Avoids double-counting)

Created field "Status" holding my own status categorization for each permit:
- Permits with a blank completion date and their date of expiry had lapsed received "Expired - Open"
- Otherwise, the permit's status was assigned "Active" unless the original StatusCurrent field was explicitly "Completed"

I added the field "AdjEstCost" for the estimated costs, adjusted for inflation, expressed in Jan, 2026 dollars. The factor of inflation drawn from BLS historical CPI data.

Address removing "expired" or "marked incomplete" permits, which may have had some work completed anyway.

{explain how it produces desirable results}

{explain what it produced}
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