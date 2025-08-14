"""Command-line interface for Moonshot POC v2.

This script reads a PDF file containing a high-level project description, runs all
registered agents via the VerboseOrchestrator, and prints verbose logs with
distinct colors for each agent. If the PDF lacks usable text, it prompts the
user to enter a description manually. Optionally, it can export results to
Google Sheets if enabled via CLI flag or environment variables.
"""

import argparse
import json
import sys
from typing import Dict

import fitz  # PyMuPDF for PDF parsing
from colorama import init, Fore, Style

from src.orchestrator import VerboseOrchestrator


def parse_pdf(path: str) -> str:
    """Extract plain text from a PDF file.

    :param path: Path to a PDF document.
    :return: Concatenated text of all pages.
    """
    try:
        doc = fitz.open(path)
    except Exception as e:
        print(f"Failed to open PDF: {e}")
        return ""
    text_parts = []
    for page in doc:
        try:
            text_parts.append(page.get_text("text"))
        except Exception:
            # ignore pages that fail to parse
            continue
    return "\n".join(filter(None, text_parts)).strip()


# Assign a unique color for each agent name.
COLOR_MAP: Dict[str, str] = {
    "Architect": Fore.RED,
    "PM": Fore.GREEN,
    "DailyCostEstimator": Fore.YELLOW,
    "Security": Fore.BLUE,
    "DevOps": Fore.MAGENTA,
    "Performance": Fore.CYAN,
    "Data": Fore.LIGHTYELLOW_EX,
    "UX": Fore.LIGHTWHITE_EX,
    "DataScientist": Fore.LIGHTCYAN_EX,
    # New dataset ML agent for ISBSG/COSMIC
    "DatasetML": Fore.LIGHTMAGENTA_EX,
}


def color_log(agent: str, prompt: str, resp: str) -> None:
    """Callback for VerboseOrchestrator that prints colored logs.

    :param agent: Friendly name of the agent.
    :param prompt: Prompt sent to the LLM.
    :param resp: Raw LLM response.
    """
    color = COLOR_MAP.get(agent, Fore.WHITE)
    # Print header with agent name
    print(color + f"\n=== {agent} ===" + Style.RESET_ALL)
    # Print prompt in dim color to reduce noise
    print(Style.DIM + "Prompt:" + Style.RESET_ALL)
    print(Style.DIM + prompt.strip() + Style.RESET_ALL + "\n")
    # Print response in assigned color
    print(color + "Response:" + Style.RESET_ALL)
    print(resp.strip() + "\n")


def main(argv: list[str] | None = None) -> None:
    """Entry point for CLI execution."""
    init(autoreset=True)  # Initialize colorama

    parser = argparse.ArgumentParser(
        description=(
            "Run Moonshot agents on a project description stored in a PDF. "
            "Displays verbose logs with colored output for each agent."
        )
    )
    parser.add_argument("pdf", help="Path to the PDF file with the project description.")
    parser.add_argument(
        "--export",
        action="store_true",
        help="Override SHEETS_EXPORT_ENABLED and export results to Google Sheets for this run.",
    )
    args = parser.parse_args(argv)

    # Extract description from PDF
    description = parse_pdf(args.pdf)
    if not description:
        description = input(
            "The PDF contained no extractable text. Please enter a project description manually:\n"
        ).strip()

    # Instantiate orchestrator with color logging
    orchestrator = VerboseOrchestrator(on_log=color_log)
    # Override export flag for this invocation if requested
    if args.export is not None:
        orchestrator._sheets_enabled = bool(args.export)

    # Run agents on the description
    try:
        results = orchestrator.run(description)
    except Exception as e:
        print(Fore.RED + f"An error occurred during processing: {e}" + Style.RESET_ALL)
        sys.exit(1)

    # Print summary JSON in neutral color
    print(Fore.WHITE + Style.BRIGHT + "===== Summary Results =====" + Style.RESET_ALL)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()