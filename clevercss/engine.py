# -*- coding: utf-8 -*-

import re
import colorsys
import operator

import consts
import utils
import errors
import expressions
import line_iterator
from errors import *

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
        lineiter = line_iterator.LineIterator(source, emit_endmarker=True)

        def fail(msg):
            raise ParserError(lineno, msg)

        def parse_definition():
            m = consts.regex['def'].search(line)
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
                        m = consts.regex['var_def'].search(line)
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
                    elif value == 'rgba':
                        return None, 'rgba'
                    elif value in consts.COLORS:
                        return value, 'color'
                except UnicodeError:
                    raise ParserError(lineno, 'invalid string escape')
                return value, 'string'

            rules = ((consts.regex['operator'], process('op')),
                     (consts.regex['call'], process('call', 1)),
                     (consts.regex['value'], lambda m: (m.groups(), 'value')),
                     (consts.regex['color'], process('color')),
                     (consts.regex['number'], process('number')),
                     (consts.regex['url'], process('url', 1)),
                     (consts.regex['string'], process_string),
                     (consts.regex['var'], lambda m: (m.group(1) or m.group(2), 'var')),
                     (consts.regex['whitespace'], None))

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
        return expressions.List(args, lineno=stream.lineno)

    def concat(self, stream):
        args = [self.add(stream)]
        while stream.current[1] != 'eof' and \
              stream.current not in ((',', 'op'), (';', 'op'),
                                     (')', 'op')):
            args.append(self.add(stream))
        if len(args) == 1:
            node = args[0]
        else:
            node = expressions.ImplicitConcat(args, lineno=stream.lineno)
        return node

    def add(self, stream):
        left = self.sub(stream)
        while stream.current == ('+', 'op'):
            stream.next()
            left = expressions.Add(left, self.sub(stream), lineno=stream.lineno)
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
            left = expressions.Mul(left, self.div(stream), lineno=stream.lineno)
        return left

    def div(self, stream):
        left = self.mod(stream)
        while stream.current == ('/', 'op'):
            stream.next()
            left = expressions.Div(left, self.mod(stream), lineno=stream.lineno)
        return left

    def mod(self, stream):
        left = self.neg(stream)
        while stream.current == ('%', 'op'):
            stream.next()
            left = expressions.Mod(left, self.neg(stream), lineno=stream.lineno)
        return left

    def neg(self, stream):
        if stream.current == ('-', 'op'):
            stream.next()
            return expressions.Neg(self.primary(stream), lineno=stream.lineno)
        return self.primary(stream)

    def primary(self, stream):
        value, token = stream.current
        if token == 'number':
            stream.next()
            node = expressions.Number(value, lineno=stream.lineno)
        elif token == 'value':
            stream.next()
            node = expressions.Value(lineno=stream.lineno, *value)
        elif token == 'color':
            stream.next()
            node = expressions.Color(value, lineno=stream.lineno)
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
                return expressions.RGB(tuple(args), lineno=stream.lineno)
            else:
                node = expressions.String('rgb')
        elif token == 'rgba':
            stream.next()
            if stream.current == ('(', 'op'):
                stream.next()
                args = []
                while len(args) < 4:
                    if args:
                        stream.expect(',', 'op')
                    args.append(self.expr(stream, True))
                stream.expect(')', 'op')
                return expressions.RGBA(args)
        elif token == 'string':
            stream.next()
            node = expressions.String(value, lineno=stream.lineno)
        elif token == 'url':
            stream.next()
            node = expressions.URL(value, lineno=stream.lineno)
        elif token == 'var':
            stream.next()
            node = expressions.Var(value, lineno=stream.lineno)
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
            node = expressions.String(value, lineno=stream.lineno)
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
        return expressions.Call(node, method, args, lineno=stream.lineno)



