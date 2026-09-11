"""Standalone entry point for RunScript(theme_picker.py), launched from
Settings > Appearance's "Preview themes..." button. Runs as its own
short-lived Kodi Python process, separate from the persistent service.py
process -- see lib/color_picker.py's docstring for why that's fine here
(same reasoning, same RunScript()-against-a-raw-file-path setup).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from lib.theme_picker import show_theme_picker  # noqa: E402

if __name__ == '__main__':
    show_theme_picker()
