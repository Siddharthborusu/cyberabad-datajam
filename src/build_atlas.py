"""Build the Hyderabad Mobility Atlas standalone HTML."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atlas.config import OUTPUT_PATH, TEMPLATE_PATH
from atlas.data import build_payload, summarize


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    payload = build_payload()
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = template.replace("__DATA__", data_json)

    OUTPUT_PATH.write_text(html, encoding="utf-8")

    summarize(payload)
    print(f"Output:          {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
