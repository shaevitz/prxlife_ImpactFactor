# PRX Life 2025 JIF Proxy

This repository computes a reproducible, open-data proxy for the **2025 Journal Impact Factor window** for **PRX Life**.

It follows the Clarivate JIF structure as closely as possible with public data:

- **Numerator:** citations made in calendar year `2025` to PRX Life items published in `2023` and `2024`
- **Denominator:** PRX Life **citable items** from `2023` and `2024`

The official Clarivate Journal Impact Factor cannot be reproduced exactly without Web of Science and Journal Citation Reports access. This project therefore labels its output as a **JIF-style proxy**, not the official JIF.

## Method

Primary calculation source:

- [OpenAlex](https://openalex.org/) for source metadata, journal works, and per-work yearly citation counts

Validation source:

- [Crossref](https://api.crossref.org/) for ISSN-level DOI counts by publication year

Default rules:

- Include only works whose primary source is **PRX Life**
- Exclude OpenAlex `preprint` records from all calculations
- Count OpenAlex `article` and `review` records in the denominator
- Count 2025 citations to **all** 2023-2024 PRX Life journal items in the numerator, regardless of cited item type

## Known Gaps Vs Clarivate

- **Coverage:** Clarivate uses Web of Science Core Collection citation coverage, not OpenAlex
- **Citable items:** Clarivate classifies citable items at the journal-section level; this project uses OpenAlex work types
- **Title normalization:** Clarivate reconciles cited-title variants internally; this project relies on OpenAlex record linkage
- **Retractions:** Clarivate's modern JIF excludes citations to and from retracted or withdrawn content; this pipeline cannot guarantee an identical exclusion policy from public data alone

## Install

```bash
python3 -m pip install -e .
```

## Usage

```bash
calculate_jif_proxy \
  --journal "PRX Life" \
  --issn 2835-8279 \
  --openalex-source-id S4387291267 \
  --jcr-year 2025 \
  --output-dir artifacts
```

The command writes:

- `artifacts/prx-life-2025-denominator.csv`
- `artifacts/prx-life-2025-numerator.csv`
- `artifacts/prx-life-2025-summary.json`
- `artifacts/prx-life-2025-report.md`
- `artifacts/raw/*.json`

## Development

Run tests:

```bash
pytest
```

Run the module directly without installing:

```bash
PYTHONPATH=src python3 -m prxlife_impact_factor.cli \
  --journal "PRX Life" \
  --issn 2835-8279 \
  --openalex-source-id S4387291267 \
  --jcr-year 2025 \
  --output-dir artifacts
```
