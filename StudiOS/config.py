"""Central settings. Edit defaults here; user changes are saved in the database."""
import os
from pathlib import Path

APP_NAME = "StudiOS"
VERSION = "0.1.0"

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA_DIR = Path(os.environ.get("STUDIOS_HOME", Path.home() / ".studios"))

DEFAULT_OLLAMA = {
    "host": "http://127.0.0.1:11434",
    "model": "llama3.2:3b",  # about 2 GB, runs on most laptops without a GPU
    "fallback_models": ["llama3.2:1b", "qwen2.5:3b", "gemma2:2b", "phi3:mini"],
    "temperature": 0.4,
    "num_ctx": 4096,
    "keep_alive": "10m",
}

# (id, label). "dashboard" is always on; the rest can be switched off in setup.
MODULES = [
    ("dashboard", "Home"),
    ("courses", "Courses"),
    ("notes", "Notes"),
    ("assistant", "Assistant"),
    ("planner", "Planner"),
    ("revision", "Revision"),
    ("tasks", "Tasks"),
    ("progress", "Progress"),
]

DEFAULT_PROFILE = {
    "name": "",
    "exam": "",
    "exam_date": "",
    "modules": [m for m, _ in MODULES],
    "setup_complete": False,
}

EXAMS = ["Class 8", "Class 9", "Class 10", "Class 11", "Class 12", "JEE", "NEET", "UPSC", "Computer Science"]
PLATFORMS = ["YouTube", "Physics Wallah", "Khan Academy", "Unacademy", "Coursera", "Custom link"]
SUBJECTS = ["Physics", "Chemistry", "Mathematics", "Biology", "English", "History", "Computer Science"]
