"""Theme catalogue and geometry. IDs are stable; skin access uses exact IDs.

Add collaborations here with attribution, styles and an explicit skin allowlist.
Never grant access using a display name, folder name, substring or caller input.
"""

from lib.theme_assets import BAKED_ASSETS, GLYPH_WIDTHS, PILL_PAD_X, PILL_PAD_Y, GLYPH_HEIGHT

FAMILIES = ('text', 'pill', 'cinema', 'madnox-collection')
THEMES = {
    'text': {'name': 'Text', 'credit': 'ScenePass', 'skins': (),
             'description': 'Clean lettering and a skip icon. Colour the whole button.'},
    'pill': {'name': 'Pill', 'credit': 'ScenePass', 'skins': (),
             'description': 'A soft capsule with independent background and lettering colours.'},
    'cinema': {'name': 'Cinema', 'credit': 'Aeon SceneCast collaboration', 'skins': ('skin.aeon.scenecast',),
               'skin_name': 'Aeon SceneCast',
               'restricted': True,
               'description': 'Cinema typography, champagne details and a soft underline glow.'},
    'madnox-collection': {'name': 'Madnox', 'credit': 'Madnox collaboration',
                          'skins': ('skin.madnox', 'skin.aeon.madnox'), 'skin_name': 'Aeon Madnox',
                          'restricted': True,
                          'description': 'Four approved Madnox designs with original red and gold artwork.'},
}
RECTANGULAR_STYLES = (
    ('solid', 'Solid rectangle', 'A filled rectangle with softly rounded corners.'),
    ('outline', 'Outlined rectangle', 'An accent border with a translucent centre.'),
    ('split', 'Split rectangle', 'A coloured icon panel beside a darker lettering area.'),
)
MODERN_STYLES = (
    ('classic', 'Solid round pill', 'A filled round pill with separate pill and lettering colours.'),
    ('round-outline', 'Outlined round pill', 'An accent border around a translucent round pill.'),
    ('round-split', 'Split round pill', 'A coloured icon panel beside a darker lettering area.'),
)
LEGACY_PILL_STYLE = ('madnox', 'Madnox logo (legacy)', 'The original full-colour Madnox logo and independent capsule lettering.')
SCENEPASS_PILL_STYLES = MODERN_STYLES + RECTANGULAR_STYLES + (LEGACY_PILL_STYLE,)

PILL_STYLES = (
    ('accent', 'Accent underline', 'Your accent colours the underline and glow.'),
    ('font', 'Coloured lettering', 'Your text colour changes the lettering. Gold details stay fixed.'),
    ('icon', 'Coloured icon', 'Your accent colours the icon. Ivory text and gold underline stay fixed.'),
    ('original', 'Original gold', 'Champagne gold and warm ivory, exactly as designed.'),
    ('accent-icon', 'Accent + icon', 'Your accent colours the icon, underline and glow. Lettering stays ivory.'),
)
TEXT_STYLES = (
    ('original', 'Original gold', 'Gold icon, warm ivory lettering and the original soft glow.'),
    ('icon-glow', 'Coloured icon + glow', 'Your accent colours the icon and glow. Lettering stays ivory.'),
)
MADNOX_STYLES = (
    ('theme-1', 'Theme 1 / Original artwork', 'Fixed red and gold artwork. No recolouring or added glow.'),
    ('theme-2', 'Theme 2 / Icon + glow', 'Colour the lettering, skip icon and glow. The complete M stays red and gold.'),
    ('theme-3', 'Theme 3 / Madnox pill', 'Colour the bold lettering inside a charcoal pill. The Madnox logo stays red and gold.'),
    ('theme-4', 'Theme 4 / Coloured 3D lettering', 'Colour the dimensional lettering. The complete M stays red and gold.'),
)
POSITION_NAMES = {1: 'Bottom right', 2: 'Bottom left', 3: 'Top left', 4: 'Top right'}
DEFAULT_COLORS = {'intro_accent': 'FFBF00', 'recap_accent': '002DB2',
                  'intro_pill_text': 'FFFFFF', 'recap_pill_text': 'FFFFFF'}


def styles(config):
    if config['theme'] == 'madnox-collection':
        return MADNOX_STYLES
    if config['theme'] == 'cinema':
        return TEXT_STYLES if config['cinema_format'] == 'text' else PILL_STYLES
    if config['theme'] == 'pill':
        return SCENEPASS_PILL_STYLES
    return (('default', 'Classic', THEMES[config['theme']]['description']),)


def selected_style(config):
    if config['theme'] == 'madnox-collection':
        value = config.get('madnox_style', 'theme-1')
        return value if value in {s[0] for s in MADNOX_STYLES} else 'theme-1'
    if config['theme'] == 'pill':
        return config['pill_style']
    if config['theme'] == 'cinema':
        value = config['cinema_' + config['cinema_format'] + '_style']
        available = TEXT_STYLES if config['cinema_format'] == 'text' else PILL_STYLES
        return value if value in {style[0] for style in available} else 'original'
    return 'default'


def color_roles(config):
    """Only controls which actually affect the selected artwork."""
    theme = config['theme']
    if theme == 'madnox-collection':
        style = selected_style(config)
        if style == 'theme-1':
            return ()
        return (('accent', 'Text, icon + glow'),) if style == 'theme-2' else (('pill_text', 'Lettering'),)
    if theme == 'text':
        return (('accent', 'Button'),)
    if theme == 'pill':
        return (('accent', 'Pill'), ('pill_text', 'Lettering'))
    style = selected_style(config)
    if style == 'original':
        return ()
    if style == 'font':
        return (('pill_text', 'Lettering'),)
    return (('accent', {'accent': 'Underline + glow', 'accent-icon': 'Accent + icon', 'icon': 'Icon',
                        'icon-glow': 'Icon + glow'}[style]),)


def layer(texture, rect, color='FFFFFFFF'):
    return {'texture': texture, 'rect': rect, 'color': color}


BUTTON_SCALE = 0.85


def asset_for(config, kind, *, playback=False):
    """Resolve the selected artwork, with sizing overrides for playback."""
    asset = _asset_for(config, kind)
    scale = BUTTON_SCALE
    if playback and config['theme'] == 'madnox-collection':
        style = selected_style(config)
        scale *= {'theme-1': .8, 'theme-2': 1, 'theme-3': .85, 'theme-4': .8}[style]
        if style == 'theme-2':
            glow, base, tint = asset['layers']
            glow['texture'] = glow['texture'].replace('_glow.png', '_playback_glow.png')
            tint['texture'] = tint['texture'].replace('_tint.png', '_playback_tint.png')
            # Give the wider lettering room while keeping the emblem at its original scale.
            emblem_offset = 28
            _, y, width, height = base['rect']
            base['rect'] = (emblem_offset, y, width, height)
            asset['width'] += emblem_offset
            bx, by, bw, bh = asset['body']
            asset['body'] = (bx, by, bw + emblem_offset, bh)
    elif playback and config['theme'] == 'pill' and config['pill_style'] == 'madnox':
        scale *= .85
    asset['width'] *= scale
    asset['height'] *= scale
    asset['body'] = tuple(value * scale for value in asset['body'])
    for item in asset['layers']:
        item['rect'] = tuple(value * scale for value in item['rect'])
    return asset


def _asset_for(config, kind):
    theme = config['theme']
    if theme == 'madnox-collection':
        style = selected_style(config)
        width, height = 400, {'theme-1': 144, 'theme-2': 112, 'theme-3': 88, 'theme-4': 144}[style]
        rect = (0, 0, width, height)
        prefix = 'themes/madnox/{}/skip_{}_'.format(style, kind)
        layers = [layer(prefix + 'base.png', rect)]
        if style != 'theme-1':
            role = '_accent' if style == 'theme-2' else '_pill_text'
            layers.append(layer(prefix + 'tint.png', rect, kind + role))
        if style == 'theme-2':
            layers.insert(0, layer(prefix + 'glow.png', rect, kind + '_accent'))
        body = (0, 0, width, height) if style == 'theme-3' else ((16, 16, 368, 80) if style == 'theme-2' else (8, 8, 384, 128))
        return {'width': width, 'height': height, 'body': body, 'layers': layers}
    if theme == 'cinema':
        fmt = config['cinema_format']
        style = selected_style(config)
        width, body_width = (359, 327) if kind == 'intro' else (381, 349)
        rect = (0, 0, width, 114)
        prefix = 'themes/cinema/{}/{}/skip_{}_{}'.format(fmt, style, kind, 'text' if fmt == 'text' else 'cinema')
        tint = kind + ('_pill_text' if style == 'font' else '_accent')
        layers = [layer(prefix + '_base.png', rect), layer(prefix + '_tint.png', rect, tint)]
        if style == 'icon-glow' or (fmt == 'pill' and style == 'accent'):
            layers.insert(0, layer('themes/cinema/glow/skip_' + kind + '_glow_soft.png', rect, kind + '_accent'))
        elif fmt == 'pill' and style == 'accent-icon':
            layers.insert(0, layer('themes/cinema/glow/skip_' + kind + '_accent_icon_soft.png', rect, kind + '_accent'))
        return {'width': width, 'height': 114, 'body': (16, 16, body_width, 82), 'layers': layers}
    if theme == 'pill' and config['pill_style'] == 'madnox':
        old = BAKED_ASSETS['pill'][kind]
        return {'width': old['width_ref'], 'height': old['height_ref'],
                'body': (0, 0, old['width_ref'], old['height_ref']),
                'layers': [layer(old['texture'], (0, 0, old['width_ref'], old['height_ref']), kind + '_accent'),
                           layer(old['glyph_texture'], old['glyph_rect_ref'], kind + '_pill_text'),
                           layer(old['logo_texture'], old['logo_rect_ref'])]}
    glyph_width = GLYPH_WIDTHS[kind]
    if theme == 'pill':
        style = selected_style(config)
        width = glyph_width + 2 * PILL_PAD_X
        height = GLYPH_HEIGHT + 2 * PILL_PAD_Y
        body = (0, 0, width, height)
        folder = 'themes/pill' if style == 'classic' else 'themes/pill/' + style
        glyph_x = PILL_PAD_X + (10 if style in ('split', 'round-split') else 0)
        return {'width': width, 'height': height, 'body': body,
                'layers': [layer(folder + '/skip_' + kind + '_pill_bg.png', body, kind + '_accent'),
                           layer('skip_' + kind + '_button.png',
                                 (glyph_x, PILL_PAD_Y, glyph_width, GLYPH_HEIGHT), kind + '_pill_text')]}
    return {'width': glyph_width, 'height': 50, 'body': (0, 0, glyph_width, 50),
            'layers': [layer('skip_' + kind + '_button.png', (0, 0, glyph_width, 50), kind + '_accent')]}


def anchor(asset, position, screen_width, screen_height, scale=1.0):
    """Anchor the body, preserving the Cinema glow outside its hit area."""
    bx, by, bw, bh = asset['body']
    left = 40 * scale if position in (2, 3) else screen_width - (40 + bw) * scale
    top = 96 * scale if position in (3, 4) else screen_height - (96 + bh) * scale
    return left - bx * scale, top - by * scale
