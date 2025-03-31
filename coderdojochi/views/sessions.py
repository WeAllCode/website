# The sessions.py file has been refactored to split the logic into multiple files for better organization and readability.
# The detailed logic for each view is now contained in separate files within the sessions directory.
# This change aims to improve maintainability and understanding of the codebase.

# Redirecting imports to the new structure
from .sessions.detail import SessionDetailView
from .sessions.signup import SessionSignUpView
from .sessions.password import PasswordSessionView
from .sessions.calendar import SessionCalendarView
