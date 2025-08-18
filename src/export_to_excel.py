import pandas as pd
from typing import Dict, Any, Iterable


def _flatten(prefix: str, obj: Any) -> Iterable[tuple[str, str]]:
    """Flatten nested dict/list structures into key-path and string value pairs."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            yield from _flatten(new_prefix, v)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_prefix = f"{prefix}[{i}]"
            yield from _flatten(new_prefix, v)
    else:
        yield (prefix, "" if obj is None else str(obj))


def export_results_to_xls(results: Dict[str, Any], file_path: str) -> None:
    """Export agent results to a flattened XLS file.

    :param results: Mapping of agent keys to their results payloads.
    :param file_path: Destination `.xls` file path.
    """
    rows: list[list[str]] = []
    for agent, payload in results.items():
        if payload is None:
            rows.append([agent, "raw", ""])
            continue
        if not isinstance(payload, (dict, list)):
            rows.append([agent, "raw", str(payload)])
            continue
        for key_path, val in _flatten("", payload):
            rows.append([agent, key_path, val])

    df = pd.DataFrame(rows, columns=["Agent", "KeyPath", "Value"])
    df.to_excel(file_path, index=False, engine="xlwt")
