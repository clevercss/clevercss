# -*- coding: utf-8 -*-

import re
import colorsys
import operator

# regular expresssions for the normal parser
_var_def_re = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)')
_def_re = re.compile(r'^([a-zA-Z-]+)\s*:\s*(.+)')
_line_comment_re = re.compile(r'(?<!:)//.*?$')

# partial regular expressions for the expr parser
_r_number = '\d+(?:\.\d+)?'
_r_string = r"(?:'(?:[^'\\]*(?:\\.[^'\\]*)*)'|" \
            r'\"(?:[^"\\]*(?:\\.[^"\\]*)*)")'
_r_call = r'([a-zA-Z_][a-zA-Z0-9_]*)\('

# regular expressions for the expr parser
_operator_re = re.compile('|'.join(re.escape(x) for x in _operators))
_whitespace_re = re.compile(r'\s+')
_number_re = re.compile(_r_number + '(?![a-zA-Z0-9_])')
_value_re = re.compile(r'(%s)(%s)(?![a-zA-Z0-9_])' % (_r_number, '|'.join(_units)))
_color_re = re.compile(r'#' + ('[a-fA-f0-9]{1,2}' * 3))
_string_re = re.compile('%s|([^\s*/();,.+$]+|\.(?!%s))+' % (_r_string, _r_call))
_url_re = re.compile(r'url\(\s*(%s|.*?)\s*\)' % _r_string)
_var_re = re.compile(r'(?<!\\)\$(?:([a-zA-Z_][a-zA-Z0-9_]*)|'
                     r'\{([a-zA-Z_][a-zA-Z0-9_]*)\})')
_call_re = re.compile(r'\.' + _r_call)


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


class ParserError(Exception):
    """
    Raised on syntax errors.
    """

    def __init__(self, lineno, message):
        self.lineno = lineno
        Exception.__init__(self, message)

    def __str__(self):
        return '%s (line %s)' % (
            self.message,
            self.lineno
        )


class EvalException(Exception):
    """
    Raised during evaluation.
    """

    def __init__(self, lineno, message):
        self.lineno = lineno
        Exception.__init__(self, message)

    def __str__(self):
        return '%s (line %s)' % (
            self.message,
            self.lineno
        )


class LineIterator(object):
    """
    This class acts as an iterator for sourcecode. It yields the lines
    without comments or empty lines and keeps track of the real line
    number.

    Example::

        >>> li = LineIterator(u'foo\nbar\n\n/* foo */bar')
        >>> li.next()
        1, u'foo'
        >>> li.next()
        2, 'bar'
        >>> li.next()
        4, 'bar'
        >>> li.next()
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        StopIteration
    """

    def __init__(self, source, emit_endmarker=False):
        """
        If `emit_endmarkers` is set to `True` the line iterator will send
        the string ``'__END__'`` before closing down.
        """
        lines = source.splitlines()
        self.lineno = 0
        self.lines = len(lines)
        self.emit_endmarker = emit_endmarker
        self._lineiter = iter(lines)

    def __iter__(self):
        return self

    def _read_line(self):
        """Read the next non empty line.  This strips line comments."""
        line = ''
        while not line.strip():
            line += _line_comment_re.sub('', self._lineiter.next()).rstrip()
            self.lineno += 1
        return line

    def _next(self):
        """
        Get the next line without mutliline comments.
        """
        # XXX: this fails for a line like this: "/* foo */bar/*"
        line = self._read_line()
        comment_start = line.find('/*')
        if comment_start < 0:
            return self.lineno, line

        stripped_line = line[:comment_start]
        comment_end = line.find('*/', comment_start)
        if comment_end >= 0:
            return self.lineno, stripped_line + line[comment_end + 2:]

        start_lineno = self.lineno
        try:
            while True:
                line = self._read_line()
                comment_end = line.find('*/')
                if comment_end >= 0:
                    stripped_line += line[comment_end + 2:]
                    break
        except StopIteration:
            raise ParserError(self.lineno, 'missing end of multiline comment')
        return start_lineno, stripped_line

    def next(self):
        """
        Get the next line without multiline comments and emit the
        endmarker if we reached the end of the sourcecode and endmarkers
        were requested.
        """
        try:
            return self._next()
        except StopIteration:
            if self.emit_endmarker:
                self.emit_endmarker = False
                return self.lineno, '__END__'
            raise


class Engine(object):
    """
    The central object that brings parser and evaluation together.  Usually
    nobody uses this because the `convert` function wraps it.
    """

    def __init__(self, source):
        self._parser = p = Parser()
        self.rules, self._vars = p.parse(source)

    def evaluate(self, context=None):
        """Evaluate code."""
        expr = None
        if not isinstance(context, dict): 
            context = {}
        for key, value in context.iteritems():
            expr = self._parser.parse_expr(1, value)
            context[key] = expr
        context.update(self._vars)

        for selectors, defs in self.rules:
            yield selectors, [(key, expr.to_string(context))
                              for key, expr in defs]

    def to_css(self, context=None):
        """Evaluate the code and generate a CSS file."""
        blocks = []
        for selectors, defs in self.evaluate(context):
            block = []
            block.append(u',\n'.join(selectors) + ' {')
            for key, value in defs:
                block.append(u'  %s: %s;' % (key, value))
            block.append('}')
            blocks.append(u'\n'.join(block))
        return u'\n\n'.join(blocks)


class TokenStream(object):
    """
    This is used by the expression parser to manage the tokens.
    """

    def __init__(self, lineno, gen):
        self.lineno = lineno
        self.gen = gen
        self.next()

    def next(self):
        try:
            self.current = self.gen.next()
        except StopIteration:
            self.current = None, 'eof'

    def expect(self, value, token):
        if self.current != (value, token):
            raise ParserError(self.lineno, "expected '%s', got '%s'." %
                              (value, self.current[0]))
        self.next()


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
        raise EvalException(self.lineno, 'cannot negate %s by %s' % self.name)

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
        return number_repr(self.value)


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
            self_unit_type = _conv_mapping.get(self.unit)
            other_unit_type = _conv_mapping.get(other.unit)
            if not self_unit_type or not other_unit_type or \
               self_unit_type != other_unit_type:
                raise EvalException(self.lineno, msg % (self.unit, other.unit)
                                    + ' because the two units are '
                                    'not compatible.')
            self_unit = _conv[self_unit_type][self.unit]
            other_unit = _conv[other_unit_type][other.unit]
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
        return number_repr(self.value) + self.unit


def brighten_color(color, context, amount=None):
    if amount is None:
        amount = Value(10.0, '%')
    hue, lightness, saturation = rgb_to_hls(*color.value)
    if isinstance(amount, Value):
        if amount.unit == '%':
            if not amount.value:
                return color
            lightness *= 1.0 + amount.value / 100.0
        else:
            raise EvalException(self.lineno, 'invalid unit %s for color '
                                'calculations.' % amount.unit)
    elif isinstance(amount, Number):
        lightness += (amount.value / 100.0)
    if lightness > 1:
        lightness = 1.0
    return Color(hls_to_rgb(hue, lightness, saturation))


def darken_color(color, context, amount=None):
    if amount is None:
        amount = Value(10.0, '%')
    hue, lightness, saturation = rgb_to_hls(*color.value)
    if isinstance(amount, Value):
        if amount.unit == '%':
            if not amount.value:
                return color
            lightness *= amount.value / 100.0
        else:
            raise EvalException(self.lineno, 'invalid unit %s for color '
                                'calculations.' % amount.unit)
    elif isinstance(amount, Number):
        lightness -= (amount.value / 100.0)
    if lightness < 0:
        lightness = 0.0
    return Color(hls_to_rgb(hue, lightness, saturation))


class Color(Literal):
    name = 'color'

    methods = {
        'brighten': brighten_color,
        'darken':   darken_color,
        'hex':      lambda x, c: Color(x.value, x.lineno)
    }

    def __init__(self, value, lineno=None):
        self.from_name = False
        if isinstance(value, basestring):
            if not value.startswith('#'):
                value = _colors.get(value)
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
        code = '#%02x%02x%02x' % self.value
        return self.from_name and _reverse_colors.get(code) or code

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
                raise EvalError(self.lineno, 'rgb components must be in '
                                'the range 0 to 255.')
            args.append(value)
        return Color(args, lineno=self.lineno)


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


class Parser(object):
    """
    Class with a bunch of methods that implement a tokenizer and parser.  In
    fact this class has two parsers.  One that splits up the code line by
    line and keeps track of indentions, and a second one for expressions in
    the value parts.
    """

    def preparse(self, source):
        """
        Do the line wise parsing and resolve indents.
        """
        rule = (None, [], [])
        vars = {}
        indention_stack = [0]
        state_stack = ['root']
        group_block_stack = []
        rule_stack = [rule]
        root_rules = rule[1]
        new_state = None
        lineiter = LineIterator(source, emit_endmarker=True)

        def fail(msg):
            raise ParserError(lineno, msg)

        def parse_definition():
            m = _def_re.search(line)
            if m is None:
                fail('invalid syntax for style definition')
            return lineiter.lineno, m.group(1), m.group(2)

        for lineno, line in lineiter:
            raw_line = line.rstrip().expandtabs()
            line = raw_line.lstrip()
            indention = len(raw_line) - len(line)

            # indenting
            if indention > indention_stack[-1]:
                if not new_state:
                    fail('unexpected indent')
                state_stack.append(new_state)
                indention_stack.append(indention)
                new_state = None

            # dedenting
            elif indention < indention_stack[-1]:
                for level in indention_stack:
                    if level == indention:
                        while indention_stack[-1] != level:
                            if state_stack[-1] == 'rule':
                                rule = rule_stack.pop()
                            elif state_stack[-1] == 'group_block':
                                name, part_defs = group_block_stack.pop()
                                for lineno, key, val in part_defs:
                                    rule[2].append((lineno, name + '-' +
                                                    key, val))
                            indention_stack.pop()
                            state_stack.pop()
                        break
                else:
                    fail('invalid dedent')

            # new state but no indention. bummer
            elif new_state:
                fail('expected definitions, found nothing')

            # end of data
            if line == '__END__':
                break

            # root and rules
            elif state_stack[-1] in ('rule', 'root'):
                # new rule blocks
                if line.endswith(':'):
                    s_rule = line[:-1].rstrip()
                    if not s_rule:
                        fail('empty rule')
                    new_state = 'rule'
                    new_rule = (s_rule, [], [])
                    rule[1].append(new_rule)
                    rule_stack.append(rule)
                    rule = new_rule

                # if we in a root block we don't consume group blocks
                # or style definitions but variable defs
                elif state_stack[-1] == 'root':
                    if '=' in line:
                        m = _var_def_re.search(line)
                        if m is None:
                            fail('invalid syntax')
                        key = m.group(1)
                        if key in vars:
                            fail('variable "%s" defined twice' % key)
                        vars[key] = (lineiter.lineno, m.group(2))
                    else:
                        fail('Style definitions or group blocks are only '
                             'allowed inside a rule or group block.')

                # definition group blocks
                elif line.endswith('->'):
                    group_prefix = line[:-2].rstrip()
                    if not group_prefix:
                        fail('no group prefix defined')
                    new_state = 'group_block'
                    group_block_stack.append((group_prefix, []))

                # otherwise parse a style definition.
                else:
                    rule[2].append(parse_definition())

            # group blocks
            elif state_stack[-1] == 'group_block':
                group_block_stack[-1][1].append(parse_definition())

            # something unparseable happened
            else:
                fail('unexpected character %s' % line[0])

        return root_rules, vars

    def parse(self, source):
        """
        Create a flat structure and parse inline expressions.
        """
        def handle_rule(rule, children, defs):
            def recurse():
                if defs:
                    result.append((get_selectors(), [
                        (k, self.parse_expr(lineno, v)) for
                        lineno, k, v in defs
                    ]))
                for child in children:
                    handle_rule(*child)

            local_rules = []
            reference_rules = []
            for r in rule.split(','):
                r = r.strip()
                if '&' in r:
                    reference_rules.append(r)
                else:
                    local_rules.append(r)

            if local_rules:
                stack.append(local_rules)
                recurse()
                stack.pop()

            if reference_rules:
                if stack:
                    parent_rules = stack.pop()
                    push_back = True
                else:
                    parent_rules = ['*']
                    push_back = False
                virtual_rules = []
                for parent_rule in parent_rules:
                    for tmpl in reference_rules:
                        virtual_rules.append(tmpl.replace('&', parent_rule))
                stack.append(virtual_rules)
                recurse()
                stack.pop()
                if push_back:
                    stack.append(parent_rules)

        def get_selectors():
            branches = [()]
            for level in stack:
                new_branches = []
                for rule in level:
                    for item in branches:
                        new_branches.append(item + (rule,))
                branches = new_branches
            return [' '.join(branch) for branch in branches]

        root_rules, vars = self.preparse(source)
        result = []
        stack = []
        for rule in root_rules:
            handle_rule(*rule)

        real_vars = {}
        for name, args in vars.iteritems():
            real_vars[name] = self.parse_expr(*args)

        return result, real_vars

    def parse_expr(self, lineno, s):
        def parse():
            pos = 0
            end = len(s)

            def process(token, group=0):
                return lambda m: (m.group(group), token)

            def process_string(m):
                value = m.group(0)
                try:
                    if value[:1] == value[-1:] and value[0] in '"\'':
                        value = value[1:-1].encode('utf-8') \
                                           .decode('string-escape') \
                                           .encode('utf-8')
                    elif value == 'rgb':
                        return None, 'rgb'
                    elif value in _colors:
                        return value, 'color'
                except UnicodeError:
                    raise ParserError(lineno, 'invalid string escape')
                return value, 'string'

            rules = ((_operator_re, process('op')),
                     (_call_re, process('call', 1)),
                     (_value_re, lambda m: (m.groups(), 'value')),
                     (_color_re, process('color')),
                     (_number_re, process('number')),
                     (_url_re, process('url', 1)),
                     (_string_re, process_string),
                     (_var_re, lambda m: (m.group(1) or m.group(2), 'var')),
                     (_whitespace_re, None))

            while pos < end:
                for rule, processor in rules:
                    m = rule.match(s, pos)
                    if m is not None:
                        if processor is not None:
                            yield processor(m)
                        pos = m.end()
                        break
                else:
                    raise ParserError(lineno, 'Syntax error')

        s = s.rstrip(';')
        return self.expr(TokenStream(lineno, parse()))

    def expr(self, stream, ignore_comma=False):
        args = [self.concat(stream)]
        list_delim = [(';', 'op')]
        if not ignore_comma:
            list_delim.append((',', 'op'))
        while stream.current in list_delim:
            stream.next()
            args.append(self.concat(stream))
        if len(args) == 1:
            return args[0]
        return List(args, lineno=stream.lineno)

    def concat(self, stream):
        args = [self.add(stream)]
        while stream.current[1] != 'eof' and \
              stream.current not in ((',', 'op'), (';', 'op'),
                                     (')', 'op')):
            args.append(self.add(stream))
        if len(args) == 1:
            node = args[0]
        else:
            node = ImplicitConcat(args, lineno=stream.lineno)
        return node

    def add(self, stream):
        left = self.sub(stream)
        while stream.current == ('+', 'op'):
            stream.next()
            left = Add(left, self.sub(stream), lineno=stream.lineno)
        return left

    def sub(self, stream):
        left = self.mul(stream)
        while stream.current == ('-', 'op'):
            stream.next()
            left = Sub(left, self.mul(stream), lineno=stream.lineno)
        return left

    def mul(self, stream):
        left = self.div(stream)
        while stream.current == ('*', 'op'):
            stream.next()
            left = Mul(left, self.div(stream), lineno=stream.lineno)
        return left

    def div(self, stream):
        left = self.mod(stream)
        while stream.current == ('/', 'op'):
            stream.next()
            left = Div(left, self.mod(stream), lineno=stream.lineno)
        return left

    def mod(self, stream):
        left = self.neg(stream)
        while stream.current == ('%', 'op'):
            stream.next()
            left = Mod(left, self.neg(stream), lineno=stream.lineno)
        return left

    def neg(self, stream):
        if stream.current == ('-', 'op'):
            stream.next()
            return Neg(self.primary(stream), lineno=stream.lineno)
        return self.primary(stream)

    def primary(self, stream):
        value, token = stream.current
        if token == 'number':
            stream.next()
            node = Number(value, lineno=stream.lineno)
        elif token == 'value':
            stream.next()
            node = Value(lineno=stream.lineno, *value)
        elif token == 'color':
            stream.next()
            node = Color(value, lineno=stream.lineno)
        elif token == 'rgb':
            stream.next()
            if stream.current == ('(', 'op'):
                stream.next()
                args = []
                while len(args) < 3:
                    if args:
                        stream.expect(',', 'op')
                    args.append(self.expr(stream, True))
                stream.expect(')', 'op')
                return RGB(tuple(args), lineno=stream.lineno)
            else:
                node = String('rgb')
        elif token == 'string':
            stream.next()
            node = String(value, lineno=stream.lineno)
        elif token == 'url':
            stream.next()
            node = URL(value, lineno=stream.lineno)
        elif token == 'var':
            stream.next()
            node = Var(value, lineno=stream.lineno)
        elif token == 'op' and value == '(':
            stream.next()
            if stream.current == (')', 'op'):
                raise ParserError(stream.lineno, 'empty parentheses are '
                                  'not valid. If you want to use them as '
                                  'string you have to quote them.')
            node = self.expr(stream)
            stream.expect(')', 'op')
        else:
            if token == 'call':
                raise ParserError(stream.lineno, 'You cannot call standalone '
                                  'methods. If you wanted to use it as a '
                                  'string you have to quote it.')
            stream.next()
            node = String(value, lineno=stream.lineno)
        while stream.current[1] == 'call':
            node = self.call(stream, node)
        return node

    def call(self, stream, node):
        method, token = stream.current
        assert token == 'call'
        stream.next()
        args = []
        while stream.current != (')', 'op'):
            if args:
                stream.expect(',', 'op')
            args.append(self.expr(stream))
        stream.expect(')', 'op')
        return Call(node, method, args, lineno=stream.lineno)


