"""Standalone entry point for RunScript(restore_position.py), launched from
Settings > Appearance's "Restore default position" button. Same setup as
restore_colors.py: puts the Skip button back at position 1 (bottom right)
and shows a brief confirmation notification.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import xbmcaddon  # noqa: E402
import xbmcgui  # noqa: E402

if __name__ == '__main__':
    xbmcaddon.Addon('service.scenepass').setSettingInt('button_position', 1)
    xbmcgui.Dialog().notification(
        'ScenePass',
        'Button position restored to bottom right',
        xbmcgui.NOTIFICATION_INFO,
        3000,
    )
