#!/usr/bin/env python

import colorsys

def number_repr(value, context):
    """
    CleverCSS uses floats internally.  To keep the string representation
    of the numbers small cut off the places if this is possible without
    losing much information.
    """
    value = str(value)
    integer, dot, fraction = value.partition('.')
    if dot and fraction == '0':
        return integer
    elif context.minified:
        return value.lstrip('0')
    else:
        return value


def rgb_to_hls(red, green, blue):
    """
    Convert RGB to HSL.  The RGB values we use are in the range 0-255, but
    HSL is in the range 0-1!
    """
    return colorsys.rgb_to_hls(red / 255.0, green / 255.0, blue / 255.0)


def hls_to_rgb(hue, saturation, lightness):
    """Convert HSL back to RGB."""
    t = colorsys.hls_to_rgb(hue, saturation, lightness)
    return tuple(int(round(x * 255)) for x in t)


def rgb_to_hsv(red, green, blue):
    """
    Converts RGB to HSV, which is more commonly used in design programs.
    """
    hsvtup = colorsys.rgb_to_hsv(red / 255.0, green / 255.0, blue / 255.0)
    return hsvtup


def hsv_to_rgb(hue, saturation, value):
    """Converts Hue/Saturation/Value back to RGB."""
    rgbtup = colorsys.hsv_to_rgb(hue, saturation, value)
    red = int(round(rgbtup[0] * 255, 0))
    green = int(round(rgbtup[1]* 255, 0))
    blue = int(round(rgbtup[2]* 255, 0))
    return (red, green, blue)

# vim: et sw=4 sts=4
