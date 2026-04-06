from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .api import JsonAPIClient, normalize_openalex_source_id


DENOMINATOR_TYPES = {"article", "review"}


@dataclass(frozen=True)
class CitationWindow:
    jcr_year: int
    citation_year: int
    publication_years: tuple[int, int]


def window_for_jcr_year(jcr_year: int) -> CitationWindow:
    return CitationWindow(
        jcr_year=jcr_year,
        citation_year=jcr_year,
        publication_years=(jcr_year - 2, jcr_year - 1),
    )


def slugify(value: str) -> str:
    cleaned = []
    previous_dash = False
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
            previous_dash = False
        elif not previous_dash:
            cleaned.append("-")
            previous_dash = True
    slug = "".join(cleaned).strip("-")
    return slug or "journal"


def extract_citations_by_year(work: dict[str, Any], year: int) -> int:
    for item in work.get("counts_by_year", []):
        if item.get("year") == year:
            return int(item.get("cited_by_count", 0))
    return 0


def is_denominator_type(work_type: str | None) -> bool:
    return (work_type or "").lower() in DENOMINATOR_TYPES


def _sort_key(work: dict[str, Any]) -> tuple[str, str, str]:
    return (
        work.get("publication_date") or "9999-12-31",
        work.get("id") or "",
        work.get("display_name") or "",
    )


def choose_preferred_work(existing: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return min([existing, candidate], key=_sort_key)


def normalize_works(
    raw_works: list[dict[str, Any]],
    source_id: str,
    citation_year: int,
) -> list[dict[str, Any]]:
    normalized_source = normalize_openalex_source_id(source_id)
    deduped_by_key: dict[str, dict[str, Any]] = {}

    for work in sorted(raw_works, key=_sort_key):
        primary_source = ((work.get("primary_location") or {}).get("source") or {})
        if primary_source.get("id") != normalized_source:
            continue

        work_type = (work.get("type") or "").lower()
        if work_type == "preprint":
            continue

        ids = work.get("ids") or {}
        doi = ids.get("doi") or work.get("doi")
        if doi:
            key = f"doi:{doi.lower()}"
        else:
            key = f"id:{work.get('id')}"

        deduped_by_key[key] = choose_preferred_work(deduped_by_key[key], work) if key in deduped_by_key else work

    rows: list[dict[str, Any]] = []
    for work in sorted(deduped_by_key.values(), key=_sort_key):
        ids = work.get("ids") or {}
        doi = ids.get("doi") or work.get("doi") or ""
        row = {
            "work_id": work.get("id", ""),
            "doi": doi,
            "title": work.get("display_name", ""),
            "publication_date": work.get("publication_date", ""),
            "publication_year": int(work.get("publication_year")),
            "type": (work.get("type") or "").lower(),
            "citations_in_target_year": extract_citations_by_year(work, citation_year),
            "included_in_denominator": is_denominator_type(work.get("type")),
        }
        rows.append(row)

    return rows


def summarize_crossref_year_counts(crossref_payload: dict[str, Any]) -> dict[int, int]:
    message = crossref_payload.get("message", {})
    breakdowns = message.get("breakdowns", {})
    values = breakdowns.get("dois-by-issued-year", [])
    return {int(year): int(count) for year, count in values}


def compute_openalex_year_counts(rows: list[dict[str, Any]]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for row in rows:
        year = int(row["publication_year"])
        counts[year] = counts.get(year, 0) + 1
    return counts


def build_summary(
    *,
    journal: str,
    issn: str,
    source_id: str,
    window: CitationWindow,
    numerator_rows: list[dict[str, Any]],
    denominator_rows: list[dict[str, Any]],
    crossref_year_counts: dict[int, int],
    openalex_year_counts: dict[int, int],
) -> dict[str, Any]:
    numerator = sum(int(row["citations_in_target_year"]) for row in numerator_rows)
    denominator = len(denominator_rows)
    jif_proxy = numerator / denominator if denominator else None

    validation_rows = []
    for year in window.publication_years:
        validation_rows.append(
            {
                "publication_year": year,
                "openalex_count": openalex_year_counts.get(year, 0),
                "crossref_count": crossref_year_counts.get(year, 0),
                "match": openalex_year_counts.get(year, 0) == crossref_year_counts.get(year, 0),
            }
        )

    return {
        "label": f"{journal} {window.jcr_year} JIF Proxy",
        "journal": journal,
        "issn": issn,
        "jcr_year": window.jcr_year,
        "target_citation_year": window.citation_year,
        "target_publication_years": list(window.publication_years),
        "numerator": numerator,
        "denominator": denominator,
        "jif_proxy": jif_proxy,
        "data_sources": {
            "primary": "OpenAlex",
            "validation": "Crossref",
            "openalex_source_id": normalize_openalex_source_id(source_id),
        },
        "assumptions": [
            "The output is a JIF-style proxy, not the official Clarivate Journal Impact Factor.",
            "OpenAlex type article/review is used as the public proxy for Clarivate citable items.",
            "Preprints are excluded from all calculations.",
            "Citations in the target year to all 2-year-window PRX Life journal items are included in the numerator.",
            "Retraction-specific exclusions cannot be guaranteed to match Clarivate exactly with public data alone.",
        ],
        "validation": validation_rows,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            {fieldname: row.get(fieldname, "") for fieldname in fieldnames}
            for row in rows
        )


def render_report(
    summary: dict[str, Any],
    denominator_rows: list[dict[str, Any]],
    numerator_rows: list[dict[str, Any]],
) -> str:
    numerator = summary["numerator"]
    denominator = summary["denominator"]
    jif_proxy = summary["jif_proxy"]
    validation = summary["validation"]
    lines = [
        f"# {summary['label']}",
        "",
        "## Result",
        "",
        f"- Numerator: **{numerator}**",
        f"- Denominator: **{denominator}**",
        f"- JIF proxy: **{jif_proxy:.6f}**" if jif_proxy is not None else "- JIF proxy: **undefined**",
        f"- Citation year: **{summary['target_citation_year']}**",
        (
            "- Cited publication years: "
            f"**{summary['target_publication_years'][0]}-{summary['target_publication_years'][1]}**"
        ),
        "",
        "## Denominator Rule",
        "",
        "OpenAlex work types `article` and `review` are counted as citable items.",
        "",
        "## Numerator Rule",
        "",
        (
            f"All non-preprint PRX Life items published in "
            f"{summary['target_publication_years'][0]}-{summary['target_publication_years'][1]} "
            f"contribute their citations received in {summary['target_citation_year']}."
        ),
        "",
        "## Coverage Validation",
        "",
        "| Publication year | OpenAlex count | Crossref count | Match |",
        "| --- | ---: | ---: | :---: |",
    ]
    for row in validation:
        lines.append(
            f"| {row['publication_year']} | {row['openalex_count']} | {row['crossref_count']} | "
            f"{'yes' if row['match'] else 'no'} |"
        )

    denominator_type_counts: dict[str, int] = {}
    for row in denominator_rows:
        denominator_type_counts[row["type"]] = denominator_type_counts.get(row["type"], 0) + 1

    numerator_type_counts: dict[str, int] = {}
    for row in numerator_rows:
        numerator_type_counts[row["type"]] = numerator_type_counts.get(row["type"], 0) + 1

    lines.extend(
        [
            "",
            "## Included Item Counts",
            "",
            f"- Denominator items by type: {json.dumps(denominator_type_counts, sort_keys=True)}",
            f"- Numerator cited-set items by type: {json.dumps(numerator_type_counts, sort_keys=True)}",
            "",
            "## Limitations",
            "",
            "- Clarivate computes the official JIF from Web of Science Core Collection, not OpenAlex.",
            "- Clarivate classifies citable items more precisely than the public OpenAlex type field.",
            "- Clarivate applies cited-title normalization and retraction handling that this public proxy cannot replicate exactly.",
            "",
        ]
    )
    return "\n".join(lines)


def run_pipeline(
    *,
    client: JsonAPIClient,
    journal: str,
    issn: str,
    source_id: str,
    jcr_year: int,
    output_dir: Path,
) -> dict[str, Any]:
    window = window_for_jcr_year(jcr_year)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    source_payload = client.fetch_openalex_source(source_id)
    crossref_payload = client.fetch_crossref_journal(issn)

    works_by_year: dict[int, list[dict[str, Any]]] = {}
    for year in window.publication_years:
        works_by_year[year] = client.fetch_openalex_works(source_id, year)

    write_json(raw_dir / "openalex_source.json", source_payload)
    write_json(raw_dir / "crossref_journal.json", crossref_payload)
    for year, works in works_by_year.items():
        write_json(raw_dir / f"openalex_works_{year}.json", works)

    raw_works = [work for year in window.publication_years for work in works_by_year[year]]
    normalized_rows = normalize_works(raw_works, source_id=source_id, citation_year=window.citation_year)
    normalized_rows = sorted(normalized_rows, key=lambda row: (row["publication_year"], row["publication_date"], row["title"]))

    denominator_rows = [row for row in normalized_rows if row["included_in_denominator"]]
    numerator_rows = normalized_rows

    crossref_year_counts = summarize_crossref_year_counts(crossref_payload)
    openalex_year_counts = compute_openalex_year_counts(normalized_rows)

    summary = build_summary(
        journal=journal,
        issn=issn,
        source_id=source_id,
        window=window,
        numerator_rows=numerator_rows,
        denominator_rows=denominator_rows,
        crossref_year_counts=crossref_year_counts,
        openalex_year_counts=openalex_year_counts,
    )

    base_name = f"{slugify(journal)}-{jcr_year}"
    denominator_fieldnames = [
        "work_id",
        "doi",
        "title",
        "publication_date",
        "publication_year",
        "type",
        "included_in_denominator",
    ]
    numerator_fieldnames = [
        "work_id",
        "doi",
        "title",
        "publication_date",
        "publication_year",
        "type",
        "citations_in_target_year",
        "included_in_denominator",
    ]

    write_csv(output_dir / f"{base_name}-denominator.csv", denominator_rows, denominator_fieldnames)
    write_csv(output_dir / f"{base_name}-numerator.csv", numerator_rows, numerator_fieldnames)
    write_json(output_dir / f"{base_name}-summary.json", summary)
    (output_dir / f"{base_name}-report.md").write_text(
        render_report(summary, denominator_rows, numerator_rows) + "\n",
        encoding="utf-8",
    )

    return summary
