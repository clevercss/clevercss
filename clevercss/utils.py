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

def tint_color(color, context, lighten=None):
    """Specifies a relative value by which to lighten the color (e.g. toward
    white). This works in the opposite manner to the brighten function; a
    value of 0% produces white (no ink); a value of 50% produces a color
    halfway between the original and white (e.g. 50% halftone). Less
    ink also means colour saturation decreases linearly with the amount of
    ink used. Only positive values between 0-100 for tints are allowed; if you
    wish to darken an existing color use the darken method or shade_color.

    N.B. real printing presses -- and therefore some software -- may produce
    slightly different saturations at different tone curves. If you're really,
    REALLY anal about the colour that gets reproduced, you should probably
    trust your design software. For most intents and purposes, though, this
    is going to be more than sufficient.

    Valueless tints will be returned unmodified.
    """
    if lighten is None:
        return color
    elif isinstance(lighten, (expressions.Value, expressions.Number)):
        lighten = lighten.value
    lighten = abs(lighten) # Positive values only!

    hue, lit, sat = rgb_to_hls(*color.value)

    # Calculate relative lightness
    lavail = 1.0 - lit
    lused = lavail - (lavail * (lighten / 100))
    lnew = lused + (1.0 - lavail)

    # Corresponding relative (de-)saturation
    if lit == 0:
        lit = 1
    snew = sat * (1 / (lnew/lit))

    return expressions.Color(hls_to_rgb(hue, lnew, snew))

def shade_color(color, context, values=None):
    """Allows specification of an absolute saturation as well as a
    relative value (lighteness) from the base color. Unlike tinting, shades
    can be either lighter OR darker than their original value; to achieve a
    darker color use a negative lightness value. Likewise, to desaturate,
    use a negative saturation.

    Because shades are not possible to acheive with print, they use the HSV
    colorspace to make modifications (instead of HSL, as is the case with
    brighten, darken, and tint_color). This may produce a different effect
    than expected, so here are a few examples:

        color.shade(0, 0)        # Original color (not modified)
        color.shade(100, 0)      # Full brightness at same saturation
        color.shade(0, 100)      # Full saturation at same brightness
        color.shade(0, -100)     # Greyscale representation of color
        color.shade(100, 100)    # Full saturation and value for this hue
        color.shade(100, -100)   # White
        color.shade(-100, [any]) # Black

    Note that some software may specify these values in reverse order (e.g.
    saturation first and value second), as well as reverse the meaning of
    values, e.g. instead of (value, saturation) these might be reported as
    (desaturation, value). A quick test should reveal if this is the case.
    """
    if values is None:
        return color
    lightness = 0.0
    saturation = 0.0
    if isinstance(values, (expressions.Value, expressions.Number, expressions.Neg)):
        values = expressions.List([values,])
    for idx, value in enumerate(values):
        if isinstance(value, (expressions.Value, expressions.Number)):
            value = value.value
        elif isinstance(value, (expressions.Neg)):
            value = -value.node.value
        if idx == 0:
            lightness = value
        if idx == 1:
            saturation = value

    hue, sat, val = rgb_to_hsv(*color.value)

    # Calculate relative Value (referred to as lightness to avoid confusion)
    if lightness >= 0:
        lavail = 1.0 - val
        lnew = val + (lavail * (lightness / 100))
    else:
        lavail = val
        lnew = lavail + (lavail * (lightness / 100))

    # Calculate relative saturation
    if saturation >= 0:
        savail = 1.0 - sat
        snew = sat + (savail * (saturation / 100))
    else:
        savail = sat
        snew = savail + (savail * (saturation / 100))

    return expressions.Color(hsv_to_rgb(hue, snew, lnew))


def mix_color(color, context, values=None):
    """
    For design purposes, related colours that share the same hue are created
    in one of two manners: They are either a result of lightening or darkening
    the original colour by some amount, or represent a mix between an original
    value and some other colour value.

    In the case of print, the latter is most frequently explicitly employed as
    a "tint", which is produced using a screen of the original colour against
    the paper background (which is nominally -- although not necessarily --
    white); see http://en.wikipedia.org/wiki/Tints_and_shades.

    Since many web page designs choose to emulate paper and adopt a white
    background, in many cases the tint function behaves as expected. However,
    in cases where a page (or related) background colour may not necessarily
    be white, a much more intuitive means of driving a new color is by mixing
    two colours together in a certain proportion, which is what this function
    does.

    Mixing black with white using an amount of 0% produces black (the original
    colour); an amount of 100% with the same colours produces white (mixcolour),
    and an amount of 50% produces a medium grey.

    Note that operations are done in the RGB color space which seems to be
    both easiest and most predictable for
    """
    if values is None:
        return color
    items = []
    try:
        for val in values:
            items.append(val)
    except TypeError:
        raise IndexError, "Two arguments are required to mix: a (second) "\
                          "color and a percentage"

    if len(items) != 2:
        raise IndexError, "Exactly two arguments are required to mix: "\
                          "a (second) color and a percentage"
    else:
        amount = abs(items[0].value)
        mixcolor = items[1]

    # Evaluate mixcolor if it's a variable.
    if isinstance(mixcolor, expressions.Var):
        mixcolor = mixcolor.evaluate(context)

    if amount == 100:
        return mixcolor
    if amount == 0:
        return color

    # Express amount as a decimal
    amount /= 100.0

    r1, g1, b1 = color.value
    r2, g2, b2 = mixcolor.value

    rnew = ((r1 * (1-amount)) + (r2 * amount))
    gnew = ((g1 * (1-amount)) + (g2 * amount))
    bnew = ((b1 * (1-amount)) + (b2 * amount))

    return expressions.Color((rnew, gnew, bnew))


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


import expressions

# vim: et sw=4 sts=4
