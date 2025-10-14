# -*- coding: utf-8 -*-
"""
Runner script for Streamlit Interface

Usage:
    python run_streamlit.py
"""

import subprocess
import sys
from pathlib import Path

# Get path to streamlit app
app_path = Path(__file__).parent / 'src' / 'interface' / 'streamlit_app.py'

print(f"[INFO] Starting Streamlit app...")
print(f"[INFO] App path: {app_path}")
print(f"[INFO] Open browser at: http://localhost:8501")
print(f"\n" + "=" * 80 + "\n")

# Run streamlit
subprocess.run([
    sys.executable,
    "-m",
    "streamlit",
    "run",
    str(app_path),
    "--server.port=8501",
    "--server.address=localhost",
    "--browser.gatherUsageStats=false"
])
