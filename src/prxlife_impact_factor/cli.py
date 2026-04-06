from __future__ import annotations

import argparse
from pathlib import Path

from .api import JsonAPIClient
from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calculate a JIF-style proxy for a journal.")
    parser.add_argument("--journal", required=True, help="Journal display name.")
    parser.add_argument("--issn", required=True, help="Journal ISSN used for Crossref validation.")
    parser.add_argument(
        "--openalex-source-id",
        required=True,
        help="OpenAlex source id, e.g. S4387291267.",
    )
    parser.add_argument(
        "--jcr-year",
        required=True,
        type=int,
        help="The JCR year to proxy. For example, 2025 uses citations made in 2025.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where artifacts will be written.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = run_pipeline(
        client=JsonAPIClient(),
        journal=args.journal,
        issn=args.issn,
        source_id=args.openalex_source_id,
        jcr_year=args.jcr_year,
        output_dir=args.output_dir,
    )
    print(
        f"{summary['label']}: numerator={summary['numerator']}, "
        f"denominator={summary['denominator']}, jif_proxy={summary['jif_proxy']:.6f}"
    )


if __name__ == "__main__":
    main()
