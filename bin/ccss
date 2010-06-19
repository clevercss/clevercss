#!/usr/bin/env python

from optparse import OptionParser
import re
import sys

import clevercss
from clevercss.errors import *

help_text = '''
usage: %prog <file 1> ... <file n>
  if called with some filenames it will read each file, cut of
  the extension and append a ".css" extension and save. If 
  the target file has the same name as the source file it will
  abort, but if it overrides a file during this process it will
  continue. This is a desired functionality. To avoid that you
  must not give your source file a .css extension.

  if you call it without arguments it will read from stdin and
  write the converted css to stdout.
'''

version_text = '''\
CleverCSS Version %s
Licensed under the BSD license.
(c) Copyright 2007 by Armin Ronacher and Georg Brandl
(c) Copyright 2010 by Jared Forsyth''' % clevercss.VERSION

def main():
    parser = OptionParser(usage=help_text, version=version_text)
    parser.add_option('--eigen-test', action='store_true',
            help='evaluate the example from the docstring')
    parser.add_option('--list-colors', action='store_true',
            help='list all known coor names')
    parser.add_option('-n', '--no-overwrite', action='store_true', dest='no_overwrite',
            help='don\'t overwrite any files (default=false)')
    parser.add_option('--to-ccss', action='store_true',
            help='convert css files to ccss')
    parser.add_option('--minified', action='store_true',
            help='minify the resulting css')

    (options, args) = parser.parse_args()
    if options.eigen_test:
        print do_test()
    elif options.list_colors:
        list_colors()
    elif options.to_ccss:
        for arg in args:
            print cleverfy(arg)
    elif len(args):
        convert_many(args, options)
    else:
        convert_stream()

import cssutils
import logging
cssutils.log.setLevel(logging.FATAL)

def parseCSS(text):
    parser = cssutils.CSSParser()
    css = parser.parseString(text)
    rules = {}
    for rule in css.cssRules:
        commas = rule.selectorText.split(',')
        for comma in commas:
            parts = comma.split()
            c = rules
            for i, part in enumerate(parts):
                if part in '>+':
                    parts[i+1] = '&' + part + parts[i+1]
                    continue
                c = c.setdefault(part, {})
            c.setdefault(':rules:', []).append(rule)
    return rules

def rulesToCCSS(selector, rules):
    text = selector + ':\n  '
    if rules.get(':rules:'):
        text += '\n\n  '.join('\n  '.join(line.strip().rstrip(';') for line in rule.style.cssText.splitlines()) for rule in rules.get(':rules:', [])) + '\n'
    for other in rules:
        if other == ':rules:':
            continue
        text += '\n  ' + rulesToCCSS(other, rules[other]).replace('\n', '\n  ')
    return text

def cleverfy(fname):
    rules = parseCSS(open(fname).read())
    text = ''
    for rule in rules:
        text += rulesToCCSS(rule, rules[rule]) + '\n\n'
    return text

def do_test():
    rx = re.compile(r'Example::\n(.*?)__END__(?ms)')
    text = rx.search(clevercss.__doc__).group(1)
    ccss = '\n'.join(line[8:].rstrip() for line in text.splitlines())
    return clevercss.convert(ccss)

def list_colors():
    print '%d known colors:' % len(clevercss.consts.COLORS)
    for color in sorted(clevercss.consts.COLORS.items()):
        print '  %-30s%s' % color

def convert_stream():
    import sys
    try:
        print clevercss.convert(sys.stdin.read())
    except (ParserError, EvalException), e:
        sys.stderr.write('Error: %s\n' % e)
        sys.exit(1)

def convert_many(files, options):
    for fname in files:
        target = fname.rsplit('.', 1)[0] + '.css'
        if fname == target:
            sys.stderr.write('Error: same name for '
                             'source and target file "%s".' % fname)
            sys.exit(2)
        elif options.no_overwrite and os.path.exists(target):
            sys.stderr.write('File exists (and --no-overwrite was used) "%s".' % target)
            sys.exit(3)

        src = open(fname)
        try:
            try:
                converted = clevercss.convert(src.read(), fname=fname)
            except (ParserError, EvalException), e:
                sys.stderr.write('Error in file %s: %s\n' % (fname, e))
                sys.exit(1)
            dst = open(target, 'w')
            try:
                print 'Writing output to %s...' % fname
                dst.write(converted)
            finally:
                dst.close()
        finally:
            src.close()

if __name__ == '__main__':
    main()

