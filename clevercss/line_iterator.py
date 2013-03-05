#!/usr/bin/env python

from clevercss import consts
from clevercss import utils

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
        lines = consts.regex['multi_comment'].sub('', source).splitlines()
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
            line += consts.regex['line_comment'].sub('', next(self._lineiter)).rstrip()
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

    def __next__(self):
        """
        Get the next line without multiline comments and emit the
        endmarker if we reached the end of the sourcecode and endmarkers
        were requested.
        """
        try:
            while True:
                lineno, stripped_line = self._next()
                if stripped_line:
                    return lineno, stripped_line
        except StopIteration:
            if self.emit_endmarker:
                self.emit_endmarker = False
                return self.lineno, '__END__'
            raise
    next = __next__


# vim: et sw=4 sts=4
