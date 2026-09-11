"""Standalone entry point for RunScript(color_picker.py, <target>), launched
from Settings > Appearance. <target> is a key from
lib/settings.py:_COLOR_SETTINGS (e.g. 'intro_accent', 'recap_pill_text').
Runs as its own short-lived Kodi Python process, separate from the persistent
service.py process -- see lib/color_picker.py for why that's fine here.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from lib.color_picker import show_color_picker  # noqa: E402

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'intro_accent'
    show_color_picker(target)
