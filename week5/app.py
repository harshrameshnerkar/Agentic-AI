"""OpsExtract AI — Enterprise Invoice Verification Center (Streamlit Launcher).

This file allows running the UI seamlessly from either:
  1) The repository root:   streamlit run week5/app.py
  2) The week5 directory:    streamlit run app.py
  3) Or directly:           streamlit run day5/streamlit_app.py
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

WEEK5_DIR = Path(__file__).resolve().parent
REPO_ROOT = WEEK5_DIR.parent
for p in (str(REPO_ROOT), str(WEEK5_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Delegate directly to the production Day 5 Streamlit application
import day5.streamlit_app as ui_app

if __name__ == "__main__":
    ui_app.main()
