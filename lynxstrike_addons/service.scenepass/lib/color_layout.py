"""Shared picker geometry and palette, in the 1920x1080 reference canvas."""
PALETTE_LIST = [
    ('Turquoise', '40E0D0'), ('Cyan', '00FFFF'), ('Pale Blue', 'AFEEEE'),
    ('Sky Blue', '87CEEB'), ('Deep Sky Blue', '00BFFF'), ('Royal Blue', '4169E1'),
    ('ScenePass Blue', '002DB2'), ('Teal', '008080'), ('Navy', '001F5B'),
    ('Mint', '98FB98'), ('Green', '00B22D'), ('Lime', '32CD32'),
    ('Chartreuse', '7FFF00'), ('Yellow Green', 'ADFF2F'), ('Lemon', 'FFF44F'),
    ('Khaki', 'F0E68C'), ('Gold', 'FFD700'), ('Amber', 'FFBF00'),
    ('Goldenrod', 'DAA520'), ('Orange', 'FFA500'), ('Dark Orange', 'FF8C00'),
    ('Orange Red', 'FF4500'), ('Red', 'FF0000'), ('Dark Red', 'B20000'),
    ('Crimson', 'DC143C'), ('Medium Purple', '9370DB'), ('Purple', '8000FF'),
    ('Magenta', 'FF00FF'), ('Hot Pink', 'FF69B4'), ('Light Pink', 'FFB6C1'),
    ('Lavender', 'E6E6FA'), ('Black', '000000'), ('Dark Grey', '404040'),
    ('Grey', '808080'), ('Silver', 'C0C0C0'), ('White', 'FFFFFF'),
]
PALETTE = {300 + i: value for i, (_, value) in enumerate(PALETTE_LIST)}
SLIDERS = {240: 'r', 241: 'g', 242: 'b'}
SLIDER_X, SLIDER_Y, SLIDER_STEP_Y, SLIDER_W, SLIDER_H = 50, 380, 76, 420, 60
TRACK_X, TRACK_W, NIB_W = 16, 240, 12
CONTROL_RECTS = {300 + i: (560 + (i % 9) * 110, 224 + (i // 9) * 110, 100, 100)
                 for i in range(36)}
CONTROL_RECTS.update({cid: (SLIDER_X, SLIDER_Y + i * SLIDER_STEP_Y, SLIDER_W, SLIDER_H)
                      for i, cid in enumerate(SLIDERS)})
CONTROL_RECTS.update({221: (50, 630, 250, 54), 222: (320, 630, 150, 54),
                      223: (1190, 860, 170, 54), 220: (1380, 860, 210, 54)})
