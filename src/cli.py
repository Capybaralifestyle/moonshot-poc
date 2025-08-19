"""Command-line interface for Moonshot POC v0.6.4.

This script reads a PDF file containing a high-level project description, runs
selected agents via the ``VerboseOrchestrator`` and prints verbose logs with
distinct colors for each agent. If the PDF lacks usable text, it prompts the
user to enter a description manually. Optionally, it can export results to an
Excel ``.xls`` file if enabled via CLI flag or environment variables. Before
running, the user selects either a local Ollama model or a cloud provider
(OpenAI, Anthropic, Kimi K2).
"""

import argparse
import json
import subprocess
import sys
from typing import Dict

import fitz  # PyMuPDF for PDF parsing
from colorama import init, Fore, Style

from src.orchestrator import VerboseOrchestrator
from src.config import get_llm


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
    "AICoding": Fore.LIGHTGREEN_EX,
    "Documentation": Fore.LIGHTBLUE_EX,
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


def _select_llm():
    """Interactively select an LLM provider and model."""
    providers = ["OLLAMA (local)", "OPENAI", "ANTHROPIC", "KIMI K2"]
    for i, p in enumerate(providers, 1):
        print(f"{i}) {p}")
    choice = input("Select provider: ").strip()
    if choice == "1":
        try:
            output = subprocess.check_output(["ollama", "list"], text=True)
            models = [line.split()[0] for line in output.splitlines()[1:] if line.strip()]
        except Exception as e:
            print(f"Failed to list Ollama models: {e}")
            sys.exit(1)
        if not models:
            print("No local models available.")
            sys.exit(1)
        for i, m in enumerate(models, 1):
            print(f"{i}) {m}")
        idx = int(input("Select model: ").strip()) - 1
        model = models[idx]
        return get_llm("ollama", model)
    mapping = {"2": "openai", "3": "anthropic", "4": "kimi"}
    provider = mapping.get(choice)
    if not provider:
        print("Invalid choice.")
        sys.exit(1)
    defaults = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-haiku-20240307",
        "kimi": "kimi-k2-instruct",
    }
    default_model = defaults[provider]
    model = input(f"Enter model name [{default_model}]: ").strip() or default_model
    return get_llm(provider, model)


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
        "--agents",
        help=(
            "Comma-separated list of agents to run (default: all)."
            " Use to batch or disable agents to control cost."
        ),
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Override XLS_EXPORT_ENABLED and export results to an XLS file for this run.",
    )
    args = parser.parse_args(argv)

    # Extract description from PDF
    description = parse_pdf(args.pdf)
    if not description:
        description = input(
            "The PDF contained no extractable text. Please enter a project description manually:\n"
        ).strip()

    # Choose LLM and instantiate orchestrator with color logging
    llm = _select_llm()
    orchestrator = VerboseOrchestrator(llm, on_log=color_log)
    # Override export flag for this invocation if requested
    if args.export is not None:
        orchestrator._xls_enabled = bool(args.export)

    selected_agents = [a.strip() for a in args.agents.split(",")] if args.agents else None

    # Run agents on the description
    try:
        results = orchestrator.run(description, agents_to_run=selected_agents)
    except Exception as e:
        print(Fore.RED + f"An error occurred during processing: {e}" + Style.RESET_ALL)
        sys.exit(1)

    # Print summary JSON in neutral color
    print(Fore.WHITE + Style.BRIGHT + "===== Summary Results =====" + Style.RESET_ALL)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
