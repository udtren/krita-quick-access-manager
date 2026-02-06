from .config_utils import get_common_config

def docker_btn_style():
    """Get docker button style"""
    config = get_common_config()
    color = config["color"]["docker_button_background_color"]
    font_color = config["color"]["docker_button_font_color"]
    font_size = config["font"]["docker_button_font_size"]
    return f"""
        QPushButton {{
            background-color: {color}; 
            color: {font_color}; 
            font-size: {font_size};
            border-radius: 6px;
            border: 1px solid #555;
            padding: 3px 6px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {lighten_color(color, 15)};
            border: 1px solid #777;
        }}
        QPushButton:pressed {{
            background-color: {darken_color(color, 15)};
            border: 1px solid #333;
        }}
    """

def shortcut_btn_style():
    # 最新のCOMMON_CONFIGを毎回参照
    config = get_common_config()
    color = config["color"]["shortcut_button_background_color"]
    font_color = config["color"]["shortcut_button_font_color"]
    font_size = config["font"]["shortcut_button_font_size"]
    return f"background-color: {color}; color: {font_color}; font-size: {font_size};"

def lighten_color(color_hex, amount):
    """Lighten a hex color by a percentage"""
    try:
        from PyQt6.QtGui import QColor
        color = QColor(color_hex)
        h, s, v, a = color.getHsv()
        v = min(255, v + amount)
        color.setHsv(h, s, v, a)
        return color.name()
    except:
        return color_hex

def darken_color(color_hex, amount):
    """Darken a hex color by a percentage"""
    try:
        from PyQt6.QtGui import QColor
        color = QColor(color_hex)
        h, s, v, a = color.getHsv()
        v = max(0, v - amount)
        color.setHsv(h, s, v, a)
        return color.name()
    except:
        return color_hex