#!/usr/bin/env python

import colorsys
import errors

def brighten_color(color, context, amount=None):
    if amount is None:
        amount = expressions.Value(10.0, '%')
    hue, lightness, saturation = rgb_to_hls(*color.value)
    if isinstance(amount, expressions.Value):
        if amount.unit == '%':
            if not amount.value:
                return color
            lightness *= 1.0 + amount.value / 100.0
        else:
            raise errors.EvalException(self.lineno, 'invalid unit %s for color '
                                'calculations.' % amount.unit)
    elif isinstance(amount, expressions.Number):
        lightness += (amount.value / 100.0)
    if lightness > 1:
        lightness = 1.0
    return expressions.Color(hls_to_rgb(hue, lightness, saturation))

def darken_color(color, context, amount=None):
    if amount is None:
        amount = expressions.Value(10.0, '%')
    hue, lightness, saturation = rgb_to_hls(*color.value)
    if isinstance(amount, expressions.Value):
        if amount.unit == '%':
            if not amount.value:
                return color
            lightness *= amount.value / 100.0
        else:
            raise errors.EvalException(self.lineno, 'invalid unit %s for color '
                                'calculations.' % amount.unit)
    elif isinstance(amount, expressions.Number):
        lightness -= (amount.value / 100.0)
    if lightness < 0:
        lightness = 0.0
    return expressions.Color(hls_to_rgb(hue, lightness, saturation))

def number_repr(value):
    """
    CleverCSS uses floats internally.  To keep the string representation
    of the numbers small cut off the places if this is possible without
    loosing much information.
    """
    value = unicode(value)
    parts = value.rsplit('.')
    if len(parts) == 2 and parts[-1] == '0':
        return parts[0]
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

import expressions

# vim: et sw=4 sts=4
