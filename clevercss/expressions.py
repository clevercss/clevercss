#!/usr/bin/env python

import os

import utils
import operator
import consts
from errors import *

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
                      self.__dict__.iteritems())
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
        rv = unicode(self.value)
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
        return utils.number_repr(self.value)

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
        return utils.number_repr(self.value) + self.unit

class Color(Literal):
    name = 'color'

    methods = {
        'brighten': utils.brighten_color,
        'darken':   utils.darken_color,
        'hex':      lambda x, c: Color(x.value, x.lineno)
    }

    def __init__(self, value, lineno=None):
        self.from_name = False
        if isinstance(value, basestring):
            if not value.startswith('#'):
                value = consts.COLORS.get(value)
                if not value:
                    raise ParserError(lineno, 'unknown color name')
                self.from_name = True
            try:
                if len(value) == 4:
                    value = [int(x * 2, 16) for x in value[1:]]
                elif len(value) == 7:
                    value = [int(value[i:i + 2], 16) for i in xrange(1, 7, 2)]
                else:
                    raise ValueError()
            except ValueError, e:
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
        if context.minified and all(x >> 4 == x & 15 for x in self.value):
            return '#%x%x%x' % tuple(x & 15 for x in self.value)
        code = '#%02x%02x%02x' % self.value
        return self.from_name and consts.REV_COLORS.get(code) or code

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
        return unicode(self.nodes)

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
                    spritemap[key] = map(int, (x1, y1, x2, y2))
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
            yield smap, smap._sprites_used.values()

class Sprite(Expr):
    name = 'Sprite'
    methods = {
        'url': lambda x, c: String("url('%s')" % x.spritemap.get_sprite_url(x)),
        'position': lambda x, c: ImplicitConcat(x._pos_vals(c)),
        'height': lambda x, c: Value(x.height, "px"),
        'width': lambda x, c: Value(x.width, "px"),
        'x1': lambda x, c: Value(x.x1, "px"),
        'y1': lambda x, c: Value(x.y1, "px"),
        'x2': lambda x, c: Value(x.x2, "px"),
        'y2': lambda x, c: Value(x.y2, "px")
    }

    def __init__(self, spritemap, name, lineno=None):
        self.lineno = lineno if lineno else name.lineno
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
        return "url('%s') -%dpx -%dpx" % (sprite_url, self.x1, self.y1)

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

    def add(self, other):
        if isinstance(other, List):
            return List(self.items + other.items, lineno=self.lineno)
        return List(self.items + [other], lineno=self.lineno)

    def to_string(self, context):
        return u', '.join(x.to_string(context) for x in self.items)

# vim: et sw=4 sts=4
