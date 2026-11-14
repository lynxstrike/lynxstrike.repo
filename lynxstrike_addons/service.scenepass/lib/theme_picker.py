"""Staged Theme Manager. Cancel writes nothing; Apply checks active skin access."""
from copy import deepcopy
import xbmc
import xbmcaddon
import xbmcgui
from lib import settings
from lib.color_picker import create_picker
from lib.theme_access import eligibility, config_eligibility, effective_config, skin_context, requirement
from lib.theme_registry import (POSITION_NAMES, DEFAULT_COLORS, MADNOX_STYLES, RECTANGULAR_STYLES,
                                MODERN_STYLES,
                                styles, selected_style, color_roles, asset_for)
from lib.theme_layout import (TICK_SIZE, FAMILY_IDS, FORMAT_IDS, SCENEPASS_MODE_IDS, STYLE_IDS, COLOR_IDS,
                              POSITION_IDS, PREVIEW, CONTROL_RECTS, FAMILY_LOGOS)
from lib.theme_render import paint
from lib.spatial_navigation import navigation_map

ADDON = xbmcaddon.Addon('service.scenepass')
ADDON_PATH = ADDON.getAddonInfo('path')
FAMILY_NAMES = {'scenepass': 'ScenePass', 'cinema': 'SceneCast', 'madnox-collection': 'Madnox'}
SCENEPASS_PILL_MODES = {'Classic': RECTANGULAR_STYLES, 'Modern': MODERN_STYLES}
LEGACY_STYLE = ('madnox', 'Theme 5 / Madnox logo (legacy)', 'The original Madnox logo with separate pill and lettering colours.')


class ThemePickerDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = settings.appearance_config()
        self.original = deepcopy(self.config)
        self.confirmed = False
        self.colors = []
        self.active_controls = []
        self.context = None
        self._child_open = False
        self._position_chosen = False
        saved_style = self.config['pill_style']
        self._scenepass_styles = {
            mode: saved_style if any(style[0] == saved_style for style in options) else options[0][0]
            for mode, options in SCENEPASS_PILL_MODES.items()
        }
        self._scenepass_mode = self._current_scenepass_mode()
        self._madnox_legacy = self.config['theme'] == 'pill' and self.config['pill_style'] == 'madnox'

    def _family(self):
        theme = self.config['theme']
        if theme == 'pill' and self.config['pill_style'] == 'madnox':
            return 'madnox-collection'
        return 'scenepass' if theme in ('pill', 'text') else theme

    def _current_scenepass_mode(self):
        if self.config['theme'] == 'text':
            return 'Text'
        if self.config['pill_style'] in {style[0] for style in RECTANGULAR_STYLES}:
            return 'Classic'
        return 'Modern'

    def _options(self):
        family = self._family()
        if family == 'madnox-collection':
            return MADNOX_STYLES + (LEGACY_STYLE,)
        if family == 'scenepass' and self.config['theme'] == 'pill':
            return SCENEPASS_PILL_MODES[self._current_scenepass_mode()]
        return styles(self.config)

    def _style_allowed(self, style):
        theme = 'madnox-collection' if style == 'madnox' else self._family()
        if theme == 'scenepass':
            return True, ''
        return eligibility(theme, self.context)

    def _select_family(self, family):
        if family == self._family():
            return
        if family == 'scenepass':
            self._select_scenepass_mode(self._scenepass_mode)
        elif family == 'madnox-collection' and self._madnox_legacy:
            self.config.update(theme='pill', pill_style='madnox')
        else:
            self.config['theme'] = family

    def _select_scenepass_mode(self, mode):
        self._scenepass_mode = mode
        if mode == 'Text':
            self.config['theme'] = 'text'
        else:
            self.config.update(theme='pill', pill_style=self._scenepass_styles[mode])

    def _label(self, cid, text, selected=False):
        self.getControl(cid).setLabel(text, textColor='FFFFCE78' if selected else 'FFF0E9DC')

    def _focus_ring(self, cid=None):
        cid = cid or self.getFocusId()
        if cid not in self.active_controls:
            return
        x, y, w, h = CONTROL_RECTS[cid]
        ring = self.getControl(690)
        ring.setPosition(x - 4, y - 4)
        ring.setWidth(w + 8)
        ring.setHeight(h + 8)
        self._focus_hint(cid)

    def _focus_hint(self, cid):
        family = next((key for key, value in FAMILY_IDS.items() if value == cid), None)
        if family == 'cinema':
            self._label(702, requirement(family))
            return
        allowed, reason = config_eligibility(self.config, self.context)
        description = next(s[2] for s in self._options() if s[0] == selected_style(self.config))
        self._label(702, description if allowed else reason)

    def _navigation(self):
        """Use spatial navigation with an explicit entry into the visible submenu."""
        rects = {cid: CONTROL_RECTS[cid] for cid in self.active_controls}
        navigation = navigation_map(rects)
        submenu = [cid for cid in (*FORMAT_IDS, *SCENEPASS_MODE_IDS, *STYLE_IDS) if cid in rects]
        if submenu:
            active_family = FAMILY_IDS[self._family()]
            for cid in FAMILY_IDS.values():
                navigation[cid]['right'] = submenu[0]
            for cid in submenu:
                if navigation[cid]['left'] not in submenu:
                    navigation[cid]['left'] = active_family
        for cid, links in navigation.items():
            self.getControl(cid).setNavigation(
                self.getControl(links['up']), self.getControl(links['down']),
                self.getControl(links['left']), self.getControl(links['right']))

    def _render(self):
        config = self.config
        theme = config['theme']
        family = self._family()
        scenepass_mode = self._current_scenepass_mode() if family == 'scenepass' else None
        self.context = skin_context()
        allowed, reason = config_eligibility(config, self.context)
        self.active_controls = list(FAMILY_IDS.values())
        for key, cid in FAMILY_IDS.items():
            self._label(cid, FAMILY_NAMES[key] + '   ›', key == family)
        x, y, _, height = CONTROL_RECTS[FAMILY_IDS[family]]
        self.getControl(695).setPosition(x - 6, y)
        self.getControl(695).setHeight(height)
        self.getControl(696).setImage(FAMILY_LOGOS[family])
        show_format = family == 'cinema'
        fmt_selected = config['cinema_format']
        for cid, fmt in FORMAT_IDS.items():
            self.getControl(cid).setVisible(show_format)
            self.getControl(cid).setEnabled(allowed)
            self._label(cid, fmt.capitalize(), fmt_selected == fmt)
            if show_format and allowed:
                self.active_controls.append(cid)
        for cid, mode in SCENEPASS_MODE_IDS.items():
            self.getControl(cid).setVisible(family == 'scenepass')
            self._label(cid, mode, mode == scenepass_mode)
            if family == 'scenepass':
                self.active_controls.append(cid)
        options = self._options()
        selected_id = selected_style(config)
        tick = self.getControl(698)
        tick.setVisible(False)
        for i, cid in enumerate(STYLE_IDS):
            visible = i < len(options) and scenepass_mode != 'Text'
            self.getControl(cid).setVisible(visible)
            if visible:
                style, name, _ = options[i]
                selectable, _ = self._style_allowed(style)
                self.getControl(cid).setEnabled(selectable)
                self._label(cid, name, style == selected_id)
                if style == selected_id:
                    sx, sy, sw, sh = CONTROL_RECTS[cid]
                    tick.setPosition(sx + sw - TICK_SIZE - 14, sy + (sh - TICK_SIZE) // 2)
                    tick.setVisible(True)
                if selectable:
                    self.active_controls.append(cid)
        _, selected_name, description = next(s for s in options if s[0] == selected_id)
        self._label(702, description if allowed else reason)
        self.colors = [(kind + '_' + role, ('Intro' if kind == 'intro' else 'Recap') + ' / ' + label)
                       for role, label in color_roles(config) for kind in ('intro', 'recap')] if allowed else []
        self._label(705, 'Fixed artwork colours' if allowed and not self.colors else '')
        for i, cid in enumerate(COLOR_IDS):
            visible = i < len(self.colors)
            self.getControl(cid).setVisible(visible)
            self.getControl(cid + 100).setVisible(visible)
            if visible:
                target, title = self.colors[i]
                self._label(cid, title)
                self.getControl(cid + 100).setColorDiffuse('FF' + config['colors'][target])
                self.active_controls.append(cid)
        for position, cid in POSITION_IDS.items():
            self._label(cid, str(position), self._position_chosen and config['position'] == position)
            self.active_controls.append(cid)
        self.getControl(663).setEnabled(allowed)
        self.getControl(661).setEnabled(bool(self.colors))
        self.active_controls += ([661] if self.colors else []) + [662] + ([663] if allowed else [])
        self._label(706, 'Unsaved changes' if self.config != self.original else '')
        self._label(707, POSITION_NAMES[config['position']])
        preview_name = selected_name
        if show_format:
            preview_name = '{} · {}'.format(fmt_selected.capitalize(), selected_name)
        elif family == 'scenepass':
            preview_name = scenepass_mode
            if scenepass_mode in SCENEPASS_PILL_MODES:
                preview_name += ' · ' + selected_name
        self._label(717, preview_name)
        self._preview()
        self._navigation()
        self._focus_ring()

    def _preview(self):
        config, _ = effective_config(self.config)
        x, y, width, height = PREVIEW
        assets = [asset_for(config, kind) for kind in ('intro', 'recap')]
        scale = width / 1920 * (1.65 if self._position_chosen else 2.3)
        gap = 12
        sample_height = sum(asset['height'] for asset in assets) * scale + gap
        position = config['position']
        top = (height - sample_height) / 2
        if self._position_chosen:
            top = 18 if position in (3, 4) else height - sample_height - 18
        for i, asset in enumerate(assets):
            sample_width = asset['width'] * scale
            left = (width - sample_width) / 2
            if self._position_chosen:
                left = 90 if position in (2, 3) else width - sample_width - 90
            paint(self, (710 + i * 3, 711 + i * 3, 712 + i * 3), asset,
                  x + left, y + top, scale, config['colors'])
            top += asset['height'] * scale + gap

    def onInit(self):
        if self._child_open:
            return
        self._render()
        cid = FAMILY_IDS[self._family()]
        self.setFocusId(cid)
        self._focus_ring(cid)

    def onClick(self, cid):
        if self._child_open:
            return
        if cid in FAMILY_IDS.values():
            self._select_family(next(key for key, value in FAMILY_IDS.items() if value == cid))
        elif cid in FORMAT_IDS and cid in self.active_controls:
            self.config['cinema_format'] = FORMAT_IDS[cid]
        elif cid in SCENEPASS_MODE_IDS and cid in self.active_controls:
            self._select_scenepass_mode(SCENEPASS_MODE_IDS[cid])
        elif cid in STYLE_IDS:
            if cid not in self.active_controls:
                return
            style = self._options()[STYLE_IDS.index(cid)][0]
            family = self._family()
            if family == 'cinema':
                self.config['cinema_' + self.config['cinema_format'] + '_style'] = style
            elif family == 'scenepass':
                self._scenepass_styles[self._scenepass_mode] = style
                self.config['pill_style'] = style
            elif family == 'madnox-collection':
                self._madnox_legacy = style == 'madnox'
                if self._madnox_legacy:
                    self.config.update(theme='pill', pill_style='madnox')
                else:
                    self.config.update(theme=family, madnox_style=style)
        elif cid in COLOR_IDS and cid in self.active_controls:
            target, title = self.colors[COLOR_IDS.index(cid)]
            picker = create_picker()
            picker.configure(target, self.config['colors'][target])
            picker.title_override = 'Skip ' + title
            picker.footer_override = 'Use colour previews your change. Apply in Theme Manager saves it.'
            self._child_open = True
            self.getControl(200).setVisible(False)
            try:
                picker.doModal()
            finally:
                self.getControl(200).setVisible(True)
                self._child_open = False
            if picker.confirmed and picker.result_hex:
                self.config['colors'][target] = picker.result_hex
            del picker
        elif cid in POSITION_IDS.values():
            self.config['position'] = next(key for key, value in POSITION_IDS.items() if value == cid)
            self._position_chosen = True
        elif cid == 661:
            for target, _ in self.colors:
                self.config['colors'][target] = DEFAULT_COLORS[target]
        elif cid == 662:
            self.close()
            return
        elif cid == 663:
            allowed, reason = config_eligibility(self.config)
            if allowed:
                settings.save_appearance(self.config)
                self.confirmed = True
                self.close()
                return
            xbmcgui.Dialog().notification('ScenePass', reason, xbmcgui.NOTIFICATION_INFO)
        self._render()
        if cid in self.active_controls:
            self.setFocusId(cid)
            self._focus_ring(cid)

    def onAction(self, action):
        if self._child_open:
            return
        if action.getId() in (10, 92):
            self.close()
            return
        if skin_context() != self.context:
            self._render()
        self._focus_ring()

    def onFocus(self, controlId):
        if not self._child_open:
            self._focus_ring(controlId)


def show_theme_picker():
    dialog = ThemePickerDialog('service.scenepass-ThemePicker.xml', ADDON_PATH, 'default', '1080i')
    dialog.doModal()
    del dialog
    xbmc.executebuiltin('Addon.OpenSettings(service.scenepass)')
    _return_to_appearance()


def _return_to_appearance():
    monitor = xbmc.Monitor()
    for _ in range(60):
        if xbmc.getCondVisibility('Window.IsActive(10140)'):
            break
        if monitor.waitForAbort(.05):
            return
    else:
        return
    if monitor.waitForAbort(.3):
        return
    xbmc.executebuiltin('SetFocus(-199)')
