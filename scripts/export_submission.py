"""
Export script to package the Skylark BI Agent project into a clean submission ZIP file.
"""

import sys
import os
import io
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_ZIP = os.path.join(PROJECT_ROOT, "skylark_monday_bi_agent_submission.zip")

EXCLUDE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    "venv",
    ".venv",
    ".system_generated",
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".DS_Store",
}


def create_submission_zip():
    print(f"Packaging submission ZIP from: {PROJECT_ROOT}")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            for file in files:
                if any(file.endswith(ext) for ext in EXCLUDE_EXTS):
                    continue
                if file.endswith(".zip"):
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PROJECT_ROOT)
                zipf.write(full_path, rel_path)
                print(f"  + {rel_path}")

    zip_size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
    print(f"\nSuccessfully created submission bundle: {OUTPUT_ZIP} ({zip_size_mb:.2f} MB)")


if __name__ == "__main__":
    create_submission_zip()
