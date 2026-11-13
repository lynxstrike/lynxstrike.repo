"""The same texture composition for manager previews and playback."""


def paint(window, controls, asset, left, top, scale, colors):
    for index, cid in enumerate(controls):
        control = window.getControl(cid)
        if index >= len(asset['layers']):
            control.setColorDiffuse('00FFFFFF')
            control.setWidth(0)
            control.setHeight(0)
            continue
        layer = asset['layers'][index]
        x, y, width, height = layer['rect']
        control.setImage(layer['texture'])
        control.setPosition(round(left + x * scale), round(top + y * scale))
        control.setWidth(round(width * scale))
        control.setHeight(round(height * scale))
        control.setColorDiffuse('FF' + colors[layer['color']] if layer['color'] in colors else layer['color'])
