import sys
from pathlib import Path

WORK = Path("/grade/work")
if "GRADE_WORK" in __import__("os").environ:
    WORK = Path(__import__("os").environ["GRADE_WORK"])

sys.path.insert(0, str(WORK))
