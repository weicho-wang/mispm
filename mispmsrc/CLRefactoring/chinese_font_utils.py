"""
Utility functions for configuring Chinese font support in matplotlib
"""

import os
import platform
import logging
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

logger = logging.getLogger(__name__)

def find_chinese_font():
    """
    Find a font on the system that supports Chinese characters
    
    Returns:
        FontProperties: A FontProperties object for the first found Chinese font,
                       or None if no suitable font is found
    """
    # Detect operating system
    os_name = platform.system()
    
    # Define potential font paths based on OS
    if os_name == 'Windows':
        potential_fonts = [
            'C:/Windows/Fonts/simsun.ttc',     # SimSun
            'C:/Windows/Fonts/simhei.ttf',     # SimHei
            'C:/Windows/Fonts/msyh.ttc',       # Microsoft YaHei
            'C:/Windows/Fonts/simkai.ttf',     # KaiTi
            'C:/Windows/Fonts/simfang.ttf',    # FangSong
            'C:/Windows/Fonts/STKAITI.ttf',    # STKaiti
        ]
    elif os_name == 'Darwin':  # macOS
        potential_fonts = [
            '/System/Library/Fonts/PingFang.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
            '/Library/Fonts/STHeiti Light.ttc',
            '/Library/Fonts/STHeiti Medium.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/STHeiti Medium.ttc',
        ]
    else:  # Linux and other Unix-like systems
        potential_fonts = [
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/truetype/arphic/uming.ttc',
            '/usr/share/fonts/truetype/arphic/ukai.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
        ]
    
    # Try to find a font that exists
    for font_path in potential_fonts:
        if os.path.exists(font_path):
            logger.info(f"Found Chinese font: {font_path}")
            return FontProperties(fname=font_path)
    
    # If no font found, return None
    logger.warning("No Chinese font found in standard locations")
    return None

def setup_matplotlib_chinese():
    """
    Configure matplotlib to properly display Chinese characters
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Try to find a Chinese font
        chinese_font = find_chinese_font()
        
        if chinese_font:
            # Set up matplotlib to use the found font
            plt.rcParams['font.family'] = chinese_font.get_name()
        else:
            # If no specific font found, use generic font families that might include Chinese
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 
                                              'WenQuanYi Micro Hei', 'PingFang SC', 'Hiragino Sans GB', 
                                              'Heiti TC', 'sans-serif']
        
        # Fix minus sign display issue
        plt.rcParams['axes.unicode_minus'] = False
        
        return True
    
    except Exception as e:
        logger.error(f"Error setting up Chinese font support: {str(e)}")
        return False

def add_chinese_text(plt_obj, x, y, text, fontsize=12, **kwargs):
    """
    Add text with Chinese characters to a matplotlib plot
    
    Args:
        plt_obj: The matplotlib plot object (plt or axes)
        x, y: Coordinates for the text
        text: The text string (can include Chinese characters)
        fontsize: Font size
        **kwargs: Additional arguments to pass to plt_obj.text()
        
    Returns:
        The text object created
    """
    try:
        # Try to find a Chinese font
        chinese_font = find_chinese_font()
        
        if chinese_font:
            # Use the specific font for this text
            text_obj = plt_obj.text(x, y, text, fontsize=fontsize, fontproperties=chinese_font, **kwargs)
        else:
            # Try with system font settings
            text_obj = plt_obj.text(x, y, text, fontsize=fontsize, **kwargs)
        
        return text_obj
        
    except Exception as e:
        logger.error(f"Error adding Chinese text: {str(e)}")
        # Fallback to basic text
        return plt_obj.text(x, y, text, fontsize=fontsize, **kwargs)
