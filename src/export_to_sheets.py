import os
import gspread
from typing import Dict, Any, Iterable
from oauth2client.service_account import ServiceAccountCredentials


def _get_client(creds_path: str):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    return gspread.authorize(creds)


def _flatten(prefix: str, obj: Any) -> Iterable[tuple[str, str]]:
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


def export_results_to_sheets(results: Dict[str, Any], sheet_name: str, creds_path: str, worksheet_index: int = 0) -> None:
    client = _get_client(creds_path)
    sh = client.open(sheet_name)
    ws = sh.get_worksheet(worksheet_index) or sh.sheet1

    ws.clear()
    ws.append_row(["Agent", "KeyPath", "Value"])

    rows = []
    for agent, payload in results.items():
        if payload is None:
            rows.append([agent, "raw", ""])
            continue
        if not isinstance(payload, (dict, list)):
            rows.append([agent, "raw", str(payload)])
            continue
        for key_path, val in _flatten("", payload):
            rows.append([agent, key_path, val])

    CHUNK = 500
    for i in range(0, len(rows), CHUNK):
        ws.append_rows(rows[i:i+CHUNK], value_input_option="RAW")