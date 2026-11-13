"""Theme Manager controls shared by the XML builder and remote navigation."""

FAMILY_IDS = {'scenepass': 601, 'cinema': 602, 'madnox-collection': 603}
FORMAT_IDS = {611: 'pill', 612: 'text'}
SCENEPASS_MODE_IDS = {613: 'Text', 614: 'Classic', 615: 'Modern'}
STYLE_IDS = tuple(range(621, 626))
COLOR_IDS = tuple(range(641, 645))
POSITION_IDS = {1: 651, 2: 652, 3: 653, 4: 654}
PREVIEW = (832, 215, 780, 439)

CONTROL_RECTS = {
    **{cid: (72, 211 + i * 77, 244, 64) for i, cid in enumerate(FAMILY_IDS.values())},
    611: (367, 292, 188, 55), 612: (570, 292, 188, 55),
    **{cid: (367 + i * 133, 292, 125, 55) for i, cid in enumerate(SCENEPASS_MODE_IDS)},
    **{cid: (385, 360 + i * 51, 373, 45) for i, cid in enumerate(STYLE_IDS)},
    **{cid: (54, 631 + i * 52, 704, 44) for i, cid in enumerate(COLOR_IDS)},
    651: (1538, 581, 56, 55), 652: (850, 581, 56, 55),
    653: (850, 233, 56, 55), 654: (1538, 233, 56, 55),
    661: (54, 862, 270, 56), 662: (1240, 862, 164, 56), 663: (1422, 862, 190, 56),
}

FAMILY_LOGOS = {
    'scenepass': 'manager/scenepass.png',
    'cinema': 'manager/scenecast.png',
    'madnox-collection': 'manager/madnox.png',
}
