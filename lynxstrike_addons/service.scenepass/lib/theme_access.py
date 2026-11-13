"""Authoritative render-time skin context, independent of script arguments."""
import xbmc
import xbmcaddon

from lib.theme_registry import THEMES


def skin_context():
    active = xbmc.getSkinDir()
    try:
        addon = xbmcaddon.Addon(active)
        installed = addon.getAddonInfo('id') == active
    except RuntimeError:
        installed = False
    return active, installed


def requirement(theme):
    return 'Selecting this theme requires {} to be installed and in use.'.format(THEMES[theme]['skin_name'])


def eligibility(theme, context=None):
    spec = THEMES[theme]
    if not spec.get('restricted'):
        return True, ''
    active, installed = context if context is not None else skin_context()
    if installed and active in spec['skins']:
        return True, ''
    return False, requirement(theme)


def effective_config(config):
    """Resolve immediately before painting. Keep the saved preference intact."""
    allowed, reason = eligibility(config['theme'])
    if allowed:
        return config, reason
    result = dict(config)
    result['theme'] = 'text'
    return result, reason
