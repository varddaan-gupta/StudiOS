"""Page registry. The dock shows pages in this order; add a module by adding a line."""
from .assistant import AssistantPage
from .courses import CoursesPage
from .dashboard import DashboardPage
from .notes import NotesPage
from .planner import PlannerPage
from .progress import ProgressPage
from .revision import RevisionPage
from .settings import SettingsPage
from .tasks import TasksPage

PAGES = {
    "dashboard": ("Home", DashboardPage),
    "courses": ("Courses", CoursesPage),
    "notes": ("Notes", NotesPage),
    "assistant": ("Assistant", AssistantPage),
    "planner": ("Planner", PlannerPage),
    "revision": ("Revision", RevisionPage),
    "tasks": ("Tasks", TasksPage),
    "progress": ("Progress", ProgressPage),
    "settings": ("Settings", SettingsPage),
}
