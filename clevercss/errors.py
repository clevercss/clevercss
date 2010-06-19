#!/usr/bin/env python

class CleverCssException(Exception):
    """Base class for exceptions raised by CleverCSS."""

    def __init__(self, lineno, message):
        self.lineno = lineno
        self.msg = message
        Exception.__init__(self, message)

    def __str__(self):
        return '%s (line %s)' % (
            self.msg,
            self.lineno
        )


class ParserError(CleverCssException):
    """Raised on syntax errors."""


class EvalException(CleverCssException):
    """Raised during evaluation."""

# vim: et sw=4 sts=4
