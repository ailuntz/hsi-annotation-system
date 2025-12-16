#!/usr/bin/env python3
"""Export OpenAPI schema to JSON file."""

import json
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


def main() -> None:
    """Export the OpenAPI schema to a JSON file."""
    openapi_schema = app.openapi()
    output_path = Path(__file__).parent.parent / "openapi.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"OpenAPI schema exported to {output_path}")


if __name__ == "__main__":
    main()
