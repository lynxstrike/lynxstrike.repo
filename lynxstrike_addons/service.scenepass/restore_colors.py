"""Standalone entry point for RunScript(restore_colors.py), launched from
Settings > Appearance's "Restore default colours" button. Runs as its own
short-lived Kodi Python process, same as color_picker.py -- see that file's
module docstring for why (and why lib/settings.py needs an explicit addon id
to work from this kind of raw-file-path RunScript() invocation).

Resets every colour in lib/settings.py:_COLOR_SETTINGS (both segment kinds'
accent colour and pill-text colour) to its default, and shows a brief
confirmation notification, since Settings > Appearance gives no other
feedback that the click did anything.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import xbmcgui  # noqa: E402

from lib.settings import restore_default_button_colors  # noqa: E402

if __name__ == '__main__':
    restore_default_button_colors()
    xbmcgui.Dialog().notification(
        'ScenePass',
        'Button colours restored to default',
        xbmcgui.NOTIFICATION_INFO,
        3000,
    )
