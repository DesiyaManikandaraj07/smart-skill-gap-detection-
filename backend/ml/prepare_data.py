"""Download / prepare Kaggle datasets when credentials are available.

Usage:
  export KAGGLE_USERNAME=... KAGGLE_KEY=...
  python ml/prepare_data.py

Without credentials, falls back to synthetic proxy data via build_proxy_labels.py.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

DATASETS = [
    # High-volume tech job postings with descriptions
    "christopherkverne/100k-us-tech-jobs-winter-2024",
    # Proxy hiring labels (synthetic ATS)
    "mobeenfatimah/resume-screening-and-ats-hiring-dataset100k-record",
]


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    try:
        import kaggle  # noqa: F401
    except ImportError:
        print("kaggle package not installed. Generating synthetic data only.")
        from build_proxy_labels import main as build

        build()
        return

    for ds in DATASETS:
        dest = RAW / ds.split("/")[-1]
        dest.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {ds} → {dest}")
        try:
            subprocess.run(
                ["kaggle", "datasets", "download", "-d", ds, "-p", str(dest), "--unzip"],
                check=True,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  Skipped {ds}: {exc}")

    from build_proxy_labels import main as build

    build()
    print("Done. Next: python ml/train.py")


if __name__ == "__main__":
    main()
