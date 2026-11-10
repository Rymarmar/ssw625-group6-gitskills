"""Compatibility entry point. The maintained Phase 3 script is code/rq1_extra.py."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parent / "code/rq1_extra.py"), run_name="__main__")
