from pathlib import Path
import sys

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from streamlit_app import *  # re-export existing app

