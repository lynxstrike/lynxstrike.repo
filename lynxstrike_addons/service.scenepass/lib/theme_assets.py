"""Shared theme geometry, in 1920x1080 reference pixels.

UHD uses twice these dimensions. PNG masters use eight times these
dimensions (four texture samples per UHD display pixel).
"""

GLYPH_HEIGHT = 50
PILL_PAD_X = 32
PILL_PAD_Y = 16
MASTER_SCALE = 8
GLYPH_WIDTHS = {'intro': 263, 'recap': 285}


def _assets():
    result = {'text': {}, 'pill': {}}
    for kind, width in GLYPH_WIDTHS.items():
        glyph = f'skip_{kind}_button.png'
        result['text'][kind] = {
            'texture': glyph, 'width_ref': width,
            'height_ref': GLYPH_HEIGHT, 'aspect': width / GLYPH_HEIGHT,
        }
        pill_w = 396
        pill_h = GLYPH_HEIGHT + 2 * PILL_PAD_Y
        result['pill'][kind] = {
            'texture': f'skip_{kind}_pill_bg.png',
            'width_ref': pill_w, 'height_ref': pill_h,
            'aspect': pill_w / pill_h,
            'glyph_texture': f'skip_{kind}_pill_text.png',
            'glyph_rect_ref': (40, 16, 210, 50),
            'logo_texture': 'madnox_logo_color.png',
            'logo_rect_ref': (232, 15, 160, 52),
        }
    return result


BAKED_ASSETS = _assets()


def asset_size(asset, scale=1.0):
    return (round(asset['width_ref'] * scale),
            round(asset['height_ref'] * scale))


def glyph_rect(asset, scale=1.0):
    rect = asset.get('glyph_rect_ref')
    return tuple(round(value * scale) for value in rect) if rect else None


def logo_rect(asset, scale=1.0):
    rect = asset.get('logo_rect_ref')
    return tuple(round(value * scale) for value in rect) if rect else None


def preview_scale(available_width, available_height):
    """One fit factor for all themes/kinds; never squeeze only the width."""
    return min(1.0, available_width / max(
        a['width_ref'] for group in BAKED_ASSETS.values() for a in group.values()),
        available_height / max(
        a['height_ref'] for group in BAKED_ASSETS.values() for a in group.values()))
