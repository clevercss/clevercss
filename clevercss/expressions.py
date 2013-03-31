#!/usr/bin/env python

import os

from clevercss import utils
import operator
from clevercss import consts
from clevercss.errors import *

class Expr(object):
    """
    Baseclass for all expressions.
    """

    #: name for exceptions
    name = 'expression'

    #: empty iterable of dict with methods
    methods = ()

    def __init__(self, lineno=None):
        self.lineno = lineno

    def evaluate(self, context):
        return self

    def add(self, other, context):
        return String(self.to_string(context) + other.to_string(context))

    def sub(self, other, context):
        raise EvalException(self.lineno, 'cannot substract %s from %s' %
                            (self.name, other.name))

    def mul(self, other, context):
        raise EvalException(self.lineno, 'cannot multiply %s with %s' %
                            (self.name, other.name))

    def div(self, other, context):
        raise EvalException(self.lineno, 'cannot divide %s by %s' %
                            (self.name, other.name))

    def mod(self, other, context):
        raise EvalException(self.lineno, 'cannot use the modulo operator for '
                            '%s and %s. Misplaced unit symbol?' %
                            (self.name, other.name))

    def neg(self, context):
        raise EvalException(self.lineno, 'cannot negate %s' % self.name)

    def to_string(self, context):
        return self.evaluate(context).to_string(context)

    def call(self, name, args, context):
        if name == 'string':
            if isinstance(self, String):
                return self
            return String(self.to_string(context))
        elif name == 'type':
            return String(self.name)
        if name not in self.methods:
            raise EvalException(self.lineno, '%s objects don\'t have a method'
                                ' called "%s". If you want to use this'
                                ' construct as string, quote it.' %
                                (self.name, name))
        return self.methods[name](self, context, *args)

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join('%s=%r' % item for item in
                      self.__dict__.items())
        )


class ImplicitConcat(Expr):
    """
    Holds multiple expressions that are delimited by whitespace.
    """
    name = 'concatenated'
    methods = {
        'list':     lambda x, c: List(x.nodes)
    }

    def __init__(self, nodes, lineno=None):
        Expr.__init__(self, lineno)
        self.nodes = nodes

    def to_string(self, context):
        return u' '.join(x.to_string(context) for x in self.nodes)

class Bin(Expr):

    def __init__(self, left, right, lineno=None):
        Expr.__init__(self, lineno)
        self.left = left
        self.right = right

class Add(Bin):

    def evaluate(self, context):
        return self.left.evaluate(context).add(
               self.right.evaluate(context), context)

class Sub(Bin):

    def evaluate(self, context):
        return self.left.evaluate(context).sub(
               self.right.evaluate(context), context)

class Mul(Bin):

    def evaluate(self, context):
        return self.left.evaluate(context).mul(
               self.right.evaluate(context), context)

class Div(Bin):

    def evaluate(self, context):
        return self.left.evaluate(context).div(
               self.right.evaluate(context), context)

class Mod(Bin):

    def evaluate(self, context):
        return self.left.evaluate(context).mod(
               self.right.evaluate(context), context)

class Neg(Expr):

    def __init__(self, node, lineno=None):
        Expr.__init__(self, lineno)
        self.node = node

    def evaluate(self, context):
        return self.node.evaluate(context).neg(context)

class Call(Expr):

    def __init__(self, node, method, args, lineno=None):
        Expr.__init__(self, lineno)
        self.node = node
        self.method = method
        self.args = args

    def evaluate(self, context):
        return self.node.evaluate(context) \
                        .call(self.method, [x.evaluate(context)
                                            for x in self.args],
                              context)

class Literal(Expr):

    def __init__(self, value, lineno=None):
        Expr.__init__(self, lineno)
        self.value = value

    def to_string(self, context):
        rv = str(self.value)
        if len(rv.split(None, 1)) > 1:
            return u"'%s'" % rv.replace('\\', '\\\\') \
                               .replace('\n', '\\\n') \
                               .replace('\t', '\\\t') \
                               .replace('\'', '\\\'')
        return rv

class Number(Literal):
    name = 'number'

    methods = {
        'abs':      lambda x, c: Number(abs(x.value)),
        'round':    lambda x, c, p=0: Number(round(x.value, p))
    }

    def __init__(self, value, lineno=None):
        Literal.__init__(self, float(value), lineno)

    def add(self, other, context):
        if isinstance(other, Number):
            return Number(self.value + other.value, lineno=self.lineno)
        elif isinstance(other, Value):
            return Value(self.value + other.value, other.unit,
                         lineno=self.lineno)
        return Literal.add(self, other, context)

    def sub(self, other, context):
        if isinstance(other, Number):
            return Number(self.value - other.value, lineno=self.lineno)
        elif isinstance(other, Value):
            return Value(self.value - other.value, other.unit,
                         lineno=self.lineno)
        return Literal.sub(self, other, context)

    def mul(self, other, context):
        if isinstance(other, Number):
            return Number(self.value * other.value, lineno=self.lineno)
        elif isinstance(other, Value):
            return Value(self.value * other.value, other.unit,
                         lineno=self.lineno)
        return Literal.mul(self, other, context)

    def div(self, other, context):
        try:
            if isinstance(other, Number):
                return Number(self.value / other.value, lineno=self.lineno)
            elif isinstance(other, Value):
                return Value(self.value / other.value, other.unit,
                             lineno=self.lineno)
            return Literal.div(self, other, context)
        except ZeroDivisionError:
            raise EvalException(self.lineno, 'cannot divide by zero')

    def mod(self, other, context):
        try:
            if isinstance(other, Number):
                return Number(self.value % other.value, lineno=self.lineno)
            elif isinstance(other, Value):
                return Value(self.value % other.value, other.unit,
                             lineno=self.lineno)
            return Literal.mod(self, other, context)
        except ZeroDivisionError:
            raise EvalException(self.lineno, 'cannot divide by zero')

    def neg(self, context):
        return Number(-self.value)

    def to_string(self, context):
        return utils.number_repr(self.value, context)

class Value(Literal):
    name = 'value'

    methods = {
        'abs':      lambda x, c: Value(abs(x.value), x.unit),
        'round':    lambda x, c, p=0: Value(round(x.value, p), x.unit)
    }

    def __init__(self, value, unit, lineno=None):
        Literal.__init__(self, float(value), lineno)
        self.unit = unit

    def add(self, other, context):
        return self._conv_calc(other, context, operator.add, Literal.add,
                               'cannot add %s and %s')

    def sub(self, other, context):
        return self._conv_calc(other, context, operator.sub, Literal.sub,
                               'cannot subtract %s from %s')

    def mul(self, other, context):
        if isinstance(other, Number):
            return Value(self.value * other.value, self.unit,
                         lineno=self.lineno)
        return Literal.mul(self, other, context)

    def div(self, other, context):
        if isinstance(other, Number):
            try:
                return Value(self.value / other.value, self.unit,
                             lineno=self.lineno)
            except ZeroDivisionError:
                raise EvalException(self.lineno, 'cannot divide by zero',
                                    lineno=self.lineno)
        return Literal.div(self, other, context)

    def mod(self, other, context):
        if isinstance(other, Number):
            try:
                return Value(self.value % other.value, self.unit,
                             lineno=self.lineno)
            except ZeroDivisionError:
                raise EvalException(self.lineno, 'cannot divide by zero')
        return Literal.mod(self, other, context)

    def _conv_calc(self, other, context, calc, fallback, msg):
        if isinstance(other, Number):
            return Value(calc(self.value, other.value), self.unit)
        elif isinstance(other, Value):
            if self.unit == other.unit:
                return Value(calc(self.value,other.value), other.unit,
                             lineno=self.lineno)
            self_unit_type = consts.CONV_mapping.get(self.unit)
            other_unit_type = consts.CONV_mapping.get(other.unit)
            if not self_unit_type or not other_unit_type or \
               self_unit_type != other_unit_type:
                raise EvalException(self.lineno, msg % (self.unit, other.unit)
                                    + ' because the two units are '
                                    'not compatible.')
            self_unit = consts.CONV[self_unit_type][self.unit]
            other_unit = consts.CONV[other_unit_type][other.unit]
            if self_unit > other_unit:
                return Value(calc(self.value / other_unit * self_unit,
                                  other.value), other.unit,
                             lineno=self.lineno)
            return Value(calc(other.value / self_unit * other_unit,
                              self.value), self.unit, lineno=self.lineno)
        return fallback(self, other, context)

    def neg(self, context):
        return Value(-self.value, self.unit, lineno=self.lineno)

    def to_string(self, context):
        return utils.number_repr(self.value, context) + self.unit

class Color(Literal):
    name = 'color'

    def brighten(self, context, amount=None):
        if amount is None:
            amount = Value(10.0, '%')
        hue, lightness, saturation = utils.rgb_to_hls(*self.value)
        if isinstance(amount, Value):
            if amount.unit == '%':
                if not amount.value:
                    return self
                lightness *= 1.0 + amount.value / 100.0
            else:
                raise errors.EvalException(self.lineno, 'invalid unit %s for color '
                                    'calculations.' % amount.unit)
        elif isinstance(amount, Number):
            lightness += (amount.value / 100.0)
        if lightness > 1:
            lightness = 1.0
        return Color(utils.hls_to_rgb(hue, lightness, saturation))

    def darken(self, context, amount=None):
        if amount is None:
            amount = Value(10.0, '%')
        hue, lightness, saturation = utils.rgb_to_hls(*self.value)
        if isinstance(amount, Value):
            if amount.unit == '%':
                if not amount.value:
                    return self
                lightness *= amount.value / 100.0
            else:
                raise errors.EvalException(self.lineno, 'invalid unit %s for color '
                                    'calculations.' % amount.unit)
        elif isinstance(amount, Number):
            lightness -= (amount.value / 100.0)
        if lightness < 0:
            lightness = 0.0
        return Color(utils.hls_to_rgb(hue, lightness, saturation))

    def tint(self, context, lighten=None):
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
            return self
        elif isinstance(lighten, (Value, Number)):
            lighten = lighten.value
        lighten = abs(lighten) # Positive values only!

        hue, lit, sat = utils.rgb_to_hls(*self.value)

        # Calculate relative lightness
        lavail = 1.0 - lit
        lused = lavail - (lavail * (lighten / 100))
        lnew = lused + (1.0 - lavail)

        # Corresponding relative (de-)saturation
        if lit == 0:
            lit = 1
        snew = sat * (1 / (lnew/lit))

        return Color(utils.hls_to_rgb(hue, lnew, snew))

    def shade(self, context, values=None):
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
            return self
        lightness = 0.0
        saturation = 0.0
        if isinstance(values, (Value, Number, Neg)):
            values = List([values,])
        for idx, value in enumerate(values):
            if isinstance(value, (Value, Number)):
                value = value.value
            elif isinstance(value, (Neg)):
                value = -value.node.value
            if idx == 0:
                lightness = value
            if idx == 1:
                saturation = value

        hue, sat, val = utils.rgb_to_hsv(*self.value)

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

        return Color(utils.hsv_to_rgb(hue, snew, lnew))


    def mix(self, context, values=None):
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
            return self
        items = []
        try:
            for val in values:
                items.append(val)
        except TypeError:
            raise IndexError("Two arguments are required to mix: a (second) "\
                            "color and a percentage")

        if len(items) != 2:
            raise IndexError("Exactly two arguments are required to mix: "\
                            "a (second) color and a percentage")
        else:
            amount = abs(items[0].value)
            mixcolor = items[1]

        # Evaluate mixcolor if it's a variable.
        if isinstance(mixcolor, Var):
            mixcolor = mixcolor.evaluate(context)

        if amount == 100:
            return mixcolor
        if amount == 0:
            return self

        # Express amount as a decimal
        amount /= 100.0

        r1, g1, b1 = self.value
        r2, g2, b2 = mixcolor.value

        rnew = ((r1 * (1-amount)) + (r2 * amount))
        gnew = ((g1 * (1-amount)) + (g2 * amount))
        bnew = ((b1 * (1-amount)) + (b2 * amount))

        return Color((rnew, gnew, bnew))

    methods = {
        'brighten': brighten,
        'darken':   darken,
        'tint':     tint,
        'shade':    shade,
        'mix':      mix,
        'hex':      lambda x, c: Color(x.value, x.lineno)
    }

    def __init__(self, value, lineno=None):
        self.from_name = False
        if isinstance(value, str):
            if not value.startswith('#'):
                value = consts.COLORS.get(value)
                if not value:
                    raise ParserError(lineno, 'unknown color name')
                self.from_name = True
            try:
                if len(value) == 4:
                    value = [int(x * 2, 16) for x in value[1:]]
                elif len(value) == 7:
                    value = [int(value[i:i + 2], 16) for i in range(1, 7, 2)]
                else:
                    raise ValueError()
            except ValueError as e:
                raise ParserError(lineno, 'invalid color value')
        Literal.__init__(self, tuple(value), lineno)

    def add(self, other, context):
        if isinstance(other, (Color, Number)):
            return self._calc(other, operator.add)
        return Literal.add(self, other, context)

    def sub(self, other, context):
        if isinstance(other, (Color, Number)):
            return self._calc(other, operator.sub)
        return Literal.sub(self, other, context)

    def mul(self, other, context):
        if isinstance(other, (Color, Number)):
            return self._calc(other, operator.mul)
        return Literal.mul(self, other, context)

    def div(self, other, context):
        if isinstance(other, (Color, Number)):
            return self._calc(other, operator.sub)
        return Literal.div(self, other, context)

    def to_string(self, context):
        code = '#%02x%02x%02x' % self.value
        if not context.minified:
            return self.from_name and consts.REV_COLORS.get(code) or code
        else:
            if all(x >> 4 == x & 15 for x in self.value):
                min_code = '#%x%x%x' % tuple(x & 15 for x in self.value)
            else:
                min_code = code
            name = consts.REV_COLORS.get(code)
            if name and len(name) < len(min_code):
                return name
            else:
                return min_code

    def _calc(self, other, method):
        is_number = isinstance(other, Number)
        channels = []
        for idx, val in enumerate(self.value):
            if is_number:
                other_val = int(other.value)
            else:
                other_val = other.value[idx]
            new_val = method(val, other_val)
            if new_val > 255:
                new_val = 255
            elif new_val < 0:
                new_val = 0
            channels.append(new_val)
        return Color(tuple(channels), lineno=self.lineno)

class RGB(Expr):
    """
    an expression that hopefully returns a Color object.
    """

    def __init__(self, rgb, lineno=None):
        Expr.__init__(self, lineno)
        self.rgb = rgb

    def evaluate(self, context):
        args = []
        for arg in self.rgb:
            arg = arg.evaluate(context)
            if isinstance(arg, Number):
                value = int(arg.value)
            elif isinstance(arg, Value) and arg.unit == '%':
                value = int(arg.value / 100.0 * 255)
            else:
                raise EvalException(self.lineno, 'colors defined using the '
                                    'rgb() literal only accept numbers and '
                                    'percentages.')
            if value < 0 or value > 255:
                raise EvalException(self.lineno, 'rgb components must be in '
                                'the range 0 to 255.')
            args.append(value)
        return Color(args, lineno=self.lineno)

class RGBA(RGB):
    """
    an expression for dealing w/ rgba colors
    """

    def to_string(self, context):
        args = []
        for i, arg in enumerate(self.rgb):
            arg = arg.evaluate(context)
            if isinstance(arg, Number):
                if i == 3:
                    value = float(arg.value)
                else:
                    value = int(arg.value)
            elif isinstance(arg, Value) and arg.unit == '%':
                if i == 3:
                    value = float(arg.value / 100.0)
                else:
                    value = int(arg.value / 100.0 * 255)
            else:
                raise EvalException(self.lineno, 'colors defined using the '
                                    'rgb() literal only accept numbers and '
                                    'percentages. (got %s)' % arg)
            if value < 0 or value > 255:
                raise EvalError(self.lineno, 'rgb components must be in '
                                'the range 0 to 255.')
            args.append(value)
        return 'rgba(%s)' % (', '.join(str(n) for n in args))

class Backstring(Literal):
    """
    A string meant to be escaped directly to output.
    """
    name = "backstring"

    def __init__(self, nodes, lineno=None):
        Expr.__init__(self, lineno)
        self.nodes = nodes

    def to_string(self, context):
        return str(self.nodes)

class String(Literal):
    name = 'string'

    methods = {
        'length':   lambda x, c: Number(len(x.value)),
        'upper':    lambda x, c: String(x.value.upper()),
        'lower':    lambda x, c: String(x.value.lower()),
        'strip':    lambda x, c: String(x.value.strip()),
        'split':    lambda x, c, d=None: String(x.value.split(d)),
        'eval':     lambda x, c: Parser().parse_expr(x.lineno, x.value)
                                         .evaluate(c)
    }

    def mul(self, other, context):
        if isinstance(other, Number):
            return String(self.value * int(other.value), lineno=self.lineno)
        return Literal.mul(self, other, context, lineno=self.lineno)

class URL(Literal):
    name = 'URL'
    methods = {
        'length':   lambda x, c: Number(len(self.value))
    }

    def add(self, other, context):
        return URL(self.value + other.to_string(context),
                   lineno=self.lineno)

    def mul(self, other, context):
        if isinstance(other, Number):
            return URL(self.value * int(other.value), lineno=self.lineno)
        return Literal.mul(self, other, context)

    def to_string(self, context):
        return 'url(%s)' % Literal.to_string(self, context)

class SpriteMap(Expr):
    name = 'SpriteMap'
    methods = {
        'sprite': lambda x, c, v: Sprite(x, v.value, lineno=v.lineno)
    }
    _magic_names = {
        "__url__": "image_url",
        "__resources__": "sprite_resource_dir",
        "__passthru__": "sprite_passthru_url",
    }

    image_url = None
    sprite_resource_dir = None
    sprite_passthru_url = None

    def __init__(self, map_fname, fname=None, lineno=None):
        Expr.__init__(self, lineno=lineno)
        self.map_fname = map_fname
        self.fname = fname

    def evaluate(self, context):
        self.map_fpath = os.path.join(os.path.dirname(self.fname),
                                      self.map_fname.to_string(context))
        self.mapping = self.read_spritemap(self.map_fpath)
        return self

    def read_spritemap(self, fpath):
        fo = open(fpath, "U")
        spritemap = {}
        try:
            for line in fo:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                rest = line.split(",")
                key = rest.pop(0).strip()
                if key[-2:] == key[:2] == "__":
                    if key not in self._magic_names:
                        raise ValueError("%r is not a valid field" % (key,))
                    att = self._magic_names[key]
                    setattr(self, att, rest[0].strip())
                elif len(rest) != 4:
                    raise ValueError("unexpected line: %r" % (line,))
                else:
                    x1, y1, x2, y2 = rest
                    spritemap[key] = [int(x) for x in (x1, y1, x2, y2)]
        finally:
            fo.close()
        return spritemap

    def get_sprite_def(self, name):
        if name in self.mapping:
            return self.mapping[name]
        elif self.sprite_passthru_url:
            return self._load_sprite(name)
        else:
            raise KeyError(name)

    def _load_sprite(self, name):
        try:
            from PIL import Image
        except ImportError:
            raise KeyError(name)

        spr_fname = os.path.join(os.path.dirname(self.map_fpath), name)
        if not os.path.exists(spr_fname):
            raise KeyError(name)

        im = Image.open(spr_fname)
        spr_def = (0, 0) + tuple(im.size)
        self.mapping[name] = spr_def
        return spr_def

    def get_sprite_url(self, sprite):
        if self.sprite_passthru_url:
            return self.sprite_passthru_url + sprite.name
        else:
            return self.image_url

    def annotate_used(self, sprite):
        pass

class AnnotatingSpriteMap(SpriteMap):
    sprite_maps = []

    def __init__(self, *args, **kwds):
        SpriteMap.__init__(self, *args, **kwds)
        self._sprites_used = {}
        self.sprite_maps.append(self)

    def read_spritemap(self, fname):
        self.image_url = "<annotator>"
        return {}

    def get_sprite_def(self, name):
        return 0, 0, 100, 100

    def get_sprite_url(self, sprite):
        return "<annotated %s>" % (sprite,)

    def annotate_used(self, sprite):
        self._sprites_used[sprite.name] = sprite

    @classmethod
    def all_used_sprites(cls):
        for smap in cls.sprite_maps:
            yield smap, list(smap._sprites_used.values())

class Sprite(Expr):
    name = 'Sprite'
    methods = {
        'url': lambda x, c: String("url(%s)" % x.spritemap.get_sprite_url(x)),
        'position': lambda x, c: ImplicitConcat(x._pos_vals(c)),
        'height': lambda x, c: Value(x.height, "px"),
        'width': lambda x, c: Value(x.width, "px"),
        'x1': lambda x, c: Value(x.x1, "px"),
        'y1': lambda x, c: Value(x.y1, "px"),
        'x2': lambda x, c: Value(x.x2, "px"),
        'y2': lambda x, c: Value(x.y2, "px")
    }

    def __init__(self, spritemap, name, lineno=None):
        if lineno:
            self.lineno = lineno
        else:
            self.lineno = name.lineno

        self.name = name
        self.spritemap = spritemap
        self.spritemap.annotate_used(self)
        try:
            self.coords = spritemap.get_sprite_def(name)
        except KeyError:
            msg = "Couldn't find sprite %r in mapping" % name
            raise EvalException(self.lineno, msg)

    def _get_coords(self):
        return self.x1, self.y1, self.x2, self.y2
    def _set_coords(self, value):
        self.x1, self.y1, self.x2, self.y2 = value
    coords = property(_get_coords, _set_coords)

    @property
    def width(self): return self.x2 - self.x1
    @property
    def height(self): return self.y2 - self.y1

    def _pos_vals(self, context):
        """Get a list of position values."""
        meths = self.methods
        call_names = "x1", "y1", "x2", "y2"
        return [meths[n](self, context) for n in call_names]

    def to_string(self, context):
        sprite_url = self.spritemap.get_sprite_url(self)
        return "url(%s) -%dpx -%dpx" % (sprite_url, self.x1, self.y1)

class Var(Expr):

    def __init__(self, name, lineno=None):
        self.name = name
        self.lineno = lineno

    def evaluate(self, context):
        if self.name not in context:
            raise EvalException(self.lineno, 'variable %s is not defined' %
                                (self.name,))
        val = context[self.name]
        context[self.name] = FailingVar(self, self.lineno)
        try:
            return val.evaluate(context)
        finally:
            context[self.name] = val

class FailingVar(Expr):

    def __init__(self, var, lineno=None):
        Expr.__init__(self, lineno or var.lineno)
        self.var = var

    def evaluate(self, context):
        raise EvalException(self.lineno, 'Circular variable dependencies '
                            'detected when resolving %s.' % (self.var.name,))

class List(Expr):
    name = 'list'

    methods = {
        'length':   lambda x, c: Number(len(x.items)),
        'join':     lambda x, c, d=String(' '): String(d.value.join(
                                 a.to_string(c) for a in x.items))
    }

    def __init__(self, items, lineno=None):
        Expr.__init__(self, lineno)
        self.items = items

    def __iter__(self):
        for item in self.items:
            yield item

    def __getslice__(self, i, j):
        return self.items[i:j]

    def __getitem__(self, i):
        return self.items[i]

    def add(self, other):
        if isinstance(other, List):
            return List(self.items + other.items, lineno=self.lineno)
        return List(self.items + [other], lineno=self.lineno)

    def to_string(self, context):
        return u', '.join(x.to_string(context) for x in self.items)

# vim: et sw=4 sts=4
