#!/usr/bin/env python

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

# vim: et sw=4 sts=4
