---
title: "PRX Life 2025 JIF Proxy: Final Report"
author: "Codex"
date: "2026-04-06"
geometry: margin=1in
fontsize: 11pt
---

# Executive Summary

This project estimated a **2025 Journal Impact Factor-style proxy** for **PRX Life** using public bibliographic data.

The result is:

- **PRX Life 2025 JIF proxy = 5.336842**
- **Numerator = 507**
- **Denominator = 95**
- Rounded to three decimals: **5.337**

Formula used:

`JIF proxy 2025 = citations made in 2025 to PRX Life items published in 2023-2024 / citable PRX Life items published in 2023-2024 = 507 / 95 = 5.336842`

This is **not** the official Clarivate Journal Impact Factor. It is a public-data reconstruction designed to match the Clarivate logic as closely as possible without access to Web of Science Core Collection or Journal Citation Reports.

# What I Did

I completed four pieces of work:

1. **Recovered the official algorithm definition from Clarivate sources.**
   Clarivate defines the Journal Impact Factor as all citations in the current JCR year to items published in the previous two years, divided by the number of scholarly items published in those same two years.

2. **Verified the status of PRX Life itself.**
   APS's public journal page shows that PRX Life currently lists `Journal Impact Factor` as `-` and says some metrics are unavailable because of the journal's recent launch and ongoing indexing in external databases. That means a public estimate is the right deliverable today.

3. **Built a reproducible calculation pipeline in the repository.**
   The code fetches source metadata and article-level records from OpenAlex, validates journal-level year counts against Crossref, classifies the denominator, computes the numerator, and writes CSV, JSON, Markdown, and raw JSON artifacts.

4. **Ran the pipeline for the 2025 JIF window.**
   The pipeline used citation year `2025` and publication years `2023-2024`, then generated the final result and supporting raw data already committed in the repo.

# How I Derived the Impact Factor Algorithm

## Clarivate's Official Structure

The core official rule comes from the Journal Citation Reports glossary:

- The **Journal Impact Factor** is all citations to the journal in the current JCR year to items published in the previous two years
- Divided by the total number of **scholarly items**
- Clarivate describes scholarly items as **articles, reviews, and proceedings papers**

Clarivate also states for the 2025 JCR release that citations **to and from retracted or withdrawn content** are excluded from the JIF numerator, while retracted articles remain in the denominator.

## Practical Translation for PRX Life

Without Clarivate data access, the closest public implementation is:

- **Target citation year:** 2025
- **Target publication years:** 2023 and 2024
- **Numerator proxy:** sum of 2025 citations to all PRX Life items from 2023-2024 available in OpenAlex
- **Denominator proxy:** count of PRX Life items from 2023-2024 whose OpenAlex type is `article` or `review`

This mirrors Clarivate's time window exactly and mirrors the numerator/denominator structure as closely as public data allows.

## Why This Mapping Is Reasonable

This method should be a good approximation because:

- It uses the exact same **2-year publication window** and **1-year citation window** as the official JIF
- It uses article-level records rather than journal-wide aggregate estimates
- It includes non-denominator items, such as editorials, in the **cited set** for the numerator, which is consistent with Clarivate's broader numerator logic
- It validates the source-year publication counts against Crossref

For PRX Life specifically, the approximation is especially clean because the 2023-2024 OpenAlex set used here contained:

- **95 articles**
- **5 editorials**
- **0 reviews**
- **0 proceedings papers**

So the denominator proxy reduces to counting articles only, while the numerator still includes citations to the five editorials.

# Raw Data and Calculation Method

## Data Sources

Primary calculation source:

- **OpenAlex** for source metadata, work metadata, and per-work yearly citation counts

Validation source:

- **Crossref** for year-by-year DOI volume checks by ISSN

Journal identifiers used:

- Journal: **PRX Life**
- ISSN: **2835-8279**
- OpenAlex source id: **S4387291267**

## Retrieved Data

The pipeline retrieved:

- OpenAlex source metadata for PRX Life
- All OpenAlex PRX Life works for publication year **2023**
- All OpenAlex PRX Life works for publication year **2024**
- Crossref journal metadata and publication-year breakdowns for ISSN `2835-8279`

Raw copies are saved in:

- `artifacts/raw/openalex_source.json`
- `artifacts/raw/openalex_works_2023.json`
- `artifacts/raw/openalex_works_2024.json`
- `artifacts/raw/crossref_journal.json`

## Normalization Rules

The pipeline then applied the following rules:

- Keep only records whose **primary source** is PRX Life
- Deduplicate first by DOI, then by work id if DOI is absent
- Exclude `preprint` records from all calculations
- Treat OpenAlex `article` and `review` as denominator-eligible
- Count citations in **2025** for every retained PRX Life item from **2023-2024**

## Validation

The year-level publication counts matched across OpenAlex and Crossref:

| Publication year | OpenAlex count | Crossref count |
| --- | ---: | ---: |
| 2023 | 32 | 32 |
| 2024 | 68 | 68 |

This is not proof of perfect record identity, but it is a useful sanity check that the public dataset capture for PRX Life is complete at the publication-year level.

# Results for PRX Life 2025

## Final Calculation

Numerator components:

- Citations made in **2025** to PRX Life items published in **2023**: **158**
- Citations made in **2025** to PRX Life items published in **2024**: **349**
- Total numerator: **507**

Denominator components:

- Citable items published in **2023**: **30**
- Citable items published in **2024**: **65**
- Total denominator: **95**

Therefore:

`PRX Life 2025 JIF proxy = 507 / 95 = 5.336842`

Rounded values:

- **5.337** to three decimals
- **5.34** to two decimals

## Composition of the Counted Sets

Numerator cited set:

- **100 total items**
- **95 articles**
- **5 editorials**

Denominator citable set:

- **95 total items**
- **95 articles**

## Most-Cited Items Within the Window

The largest 2025 citation contributions in the 2023-2024 window were:

| 2025 citations | Publication year | Title |
| ---: | ---: | --- |
| 17 | 2024 | *Uncovering Universal Characteristics of Homing Paths using Foraging Robots* |
| 16 | 2024 | *Molecular Drivers of Aging in Biomolecular Condensates: Desolvation, Rigidification, and Sticker Lifetimes* |
| 14 | 2023 | *Models of Cell Processes are Far from the Edge of Chaos* |
| 12 | 2023 | *Interplay between Mechanochemical Patterning and Glassy Dynamics in Cellular Monolayers* |
| 12 | 2023 | *Tissue Flows Are Tuned by Actomyosin-Dependent Mechanics in Developing Embryos* |

# Why This Works

This calculation is credible because it reconstructs the **shape** of the official JIF rather than inventing a new journal metric.

It works by preserving the essential Clarivate logic:

- same citation year
- same 2-year cited-publication window
- same numerator-over-denominator structure
- denominator limited to scholarly/citable items
- numerator allowed to include citations to the broader journal content set

The main reason the number can still differ from an eventual official Clarivate JIF is not the formula. The main reason is the **database**.

Clarivate's official value is computed from:

- Web of Science Core Collection coverage
- Clarivate's own cited-reference linking
- Clarivate's own citable-item classification
- Clarivate's own retraction flags and exclusions

This proxy instead uses:

- OpenAlex record linkage and yearly citation counts
- Crossref for a publication-count validation check

So the proxy should be interpreted as:

- a **good-faith reconstruction of the official method**
- likely directionally close
- not guaranteed to equal the eventual Clarivate number exactly

# Limitations

The main limitations are:

1. **Database coverage differences**
   OpenAlex and Web of Science do not index exactly the same citing documents.

2. **Citable-item classification differences**
   Clarivate classifies citable content at a finer level than OpenAlex's top-level type labels.

3. **Citation-linking differences**
   Clarivate performs its own cited-title normalization and record linking.

4. **Retraction-policy mismatch risk**
   Clarivate's 2025 JIF excludes citations to and from retracted content in the numerator. This public pipeline cannot guarantee an identical exclusion set.

5. **No direct JCR verification**
   Because PRX Life does not currently display an official JIF on APS's public page, this result cannot yet be checked against the eventual official value.

# Repository Outputs

The implementation and generated outputs are in the repository:

- `src/prxlife_impact_factor/`
- `tests/`
- `artifacts/prx-life-2025-numerator.csv`
- `artifacts/prx-life-2025-denominator.csv`
- `artifacts/prx-life-2025-summary.json`
- `artifacts/prx-life-2025-report.md`
- `artifacts/prx-life-2025-final-report.md`
- `artifacts/prx-life-2025-final-report.pdf`

The CLI used for reproducibility is:

```bash
calculate_jif_proxy \
  --journal "PRX Life" \
  --issn 2835-8279 \
  --openalex-source-id S4387291267 \
  --jcr-year 2025 \
  --output-dir artifacts
```

# Conclusion

Using the Clarivate JIF structure and the best available public raw data, the estimated **PRX Life 2025 Journal Impact Factor proxy** is:

**5.336842**

This should be read as the strongest reproducible public estimate currently available from open data, not as the official Clarivate metric.

# Sources

1. Clarivate, *Journal Citation Reports Glossary*  
   <https://journalcitationreports.zendesk.com/hc/en-gb/articles/28351666061457-Glossary>

2. Clarivate, *Journal Citation Reports 2025: Addressing retractions and strengthening research integrity*  
   <https://clarivate.com/academia-government/blog/journal-citation-reports-2025-addressing-retractions-and-strengthening-research-integrity/>

3. APS, *PRX Life - About PRX Life*  
   <https://journals.aps.org/prxlife/about>

4. OpenAlex source record for PRX Life  
   <https://api.openalex.org/sources/S4387291267>

5. Crossref journal record for PRX Life  
   <https://api.crossref.org/journals/2835-8279>
