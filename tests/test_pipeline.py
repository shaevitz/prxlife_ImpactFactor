from __future__ import annotations

import json
from pathlib import Path

from prxlife_impact_factor.pipeline import (
    is_denominator_type,
    normalize_works,
    run_pipeline,
    window_for_jcr_year,
)


FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FakeClient:
    def fetch_openalex_source(self, source_id: str):
        return load_fixture("openalex_source.json")

    def fetch_crossref_journal(self, issn: str):
        return load_fixture("crossref_journal.json")

    def fetch_openalex_works(self, source_id: str, publication_year: int):
        return load_fixture(f"openalex_works_{publication_year}.json")


def test_window_for_jcr_year():
    window = window_for_jcr_year(2025)
    assert window.citation_year == 2025
    assert window.publication_years == (2023, 2024)


def test_denominator_type_rules():
    assert is_denominator_type("article")
    assert is_denominator_type("review")
    assert not is_denominator_type("editorial")
    assert not is_denominator_type("preprint")


def test_normalize_works_dedupes_by_doi_and_excludes_preprints():
    duplicate = {
        "id": "https://openalex.org/W999",
        "display_name": "Article One Duplicate",
        "publication_year": 2023,
        "publication_date": "2023-08-01",
        "type": "article",
        "doi": "https://doi.org/10.1000/article-one",
        "ids": {"doi": "https://doi.org/10.1000/article-one"},
        "counts_by_year": [{"year": 2025, "cited_by_count": 99}],
        "primary_location": {
            "source": {
                "id": "https://openalex.org/S4387291267",
                "display_name": "PRX Life",
            }
        },
    }
    rows = normalize_works(
        raw_works=load_fixture("openalex_works_2023.json") + [duplicate] + load_fixture("openalex_works_2024.json"),
        source_id="S4387291267",
        citation_year=2025,
    )

    assert len(rows) == 4
    titles = {row["title"] for row in rows}
    assert "Preprint One" not in titles
    assert "Article One Duplicate" not in titles


def test_numerator_uses_only_target_year_citations():
    rows = normalize_works(
        raw_works=load_fixture("openalex_works_2023.json"),
        source_id="S4387291267",
        citation_year=2025,
    )
    row_by_title = {row["title"]: row for row in rows}
    assert row_by_title["Article One"]["citations_in_target_year"] == 3
    assert row_by_title["Editorial One"]["citations_in_target_year"] == 1


def test_run_pipeline_writes_expected_outputs(tmp_path: Path):
    summary = run_pipeline(
        client=FakeClient(),
        journal="PRX Life",
        issn="2835-8279",
        source_id="S4387291267",
        jcr_year=2025,
        output_dir=tmp_path,
    )

    assert summary["numerator"] == 10
    assert summary["denominator"] == 3
    assert abs(summary["jif_proxy"] - (10 / 3)) < 1e-9

    denominator_csv = tmp_path / "prx-life-2025-denominator.csv"
    numerator_csv = tmp_path / "prx-life-2025-numerator.csv"
    summary_json = tmp_path / "prx-life-2025-summary.json"
    report_md = tmp_path / "prx-life-2025-report.md"

    assert denominator_csv.exists()
    assert numerator_csv.exists()
    assert summary_json.exists()
    assert report_md.exists()

    on_disk = json.loads(summary_json.read_text(encoding="utf-8"))
    assert on_disk["numerator"] == 10
    assert on_disk["denominator"] == 3

    numerator_lines = numerator_csv.read_text(encoding="utf-8").strip().splitlines()
    denominator_lines = denominator_csv.read_text(encoding="utf-8").strip().splitlines()
    assert len(numerator_lines) == 5
    assert len(denominator_lines) == 4

    report_text = report_md.read_text(encoding="utf-8")
    assert "PRX Life 2025 JIF Proxy" in report_text
    assert "| 2023 | 2 | 2 | yes |" in report_text
    assert "| 2024 | 2 | 3 | no |" in report_text
