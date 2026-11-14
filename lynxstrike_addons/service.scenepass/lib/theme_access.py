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


def access_theme(config):
    """The collaboration a saved config belongs to. Theme 5 is stored as a Pill style
    but is Madnox artwork, so it needs the Madnox skin like the other Madnox themes."""
    if config['theme'] == 'pill' and config.get('pill_style') == 'madnox':
        return 'madnox-collection'
    return config['theme']


def config_eligibility(config, context=None):
    return eligibility(access_theme(config), context)


def effective_config(config):
    """Resolve immediately before painting. Keep the saved preference intact."""
    allowed, reason = config_eligibility(config)
    if allowed:
        return config, reason
    result = dict(config)
    result['theme'] = 'text'
    return result, reason
