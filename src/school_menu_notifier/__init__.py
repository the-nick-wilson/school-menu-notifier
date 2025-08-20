"""
School Menu Notifier

A Python package for automatically fetching and emailing school lunch menus.
"""

__version__ = "1.0.0"
__author__ = "Nick Wilson"

from .daily_notifier import SchoolMenuNotifier
from .weekly_notifier import WeeklySchoolMenuNotifier

__all__ = ["SchoolMenuNotifier", "WeeklySchoolMenuNotifier"]
