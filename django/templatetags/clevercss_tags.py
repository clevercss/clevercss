import sys, os
from django import template
import settings
from meetings.deps.clevercss import convert, ParserError, EvalException


register = template.Library()

@register.filter(name='clevercss')
def do_clevercss(fn):
    '''
    Create css from ccss and return its path

    Requires settings.MEDIA_ROOT, settings.MEDIA_URL
    '''

    css_name = fn.rsplit('.', 1)[0]
    css_url = os.path.join(settings.MEDIA_URL, 'css', css_name +'.css')

    fn = os.path.join(settings.MEDIA_ROOT, 'css', fn)
    target = fn.rsplit('.', 1)[0] + '.css'

    if fn == target:
        sys.stderr.write('Error: same name for source and target file'
                         ' "%s".' % fn)
        sys.exit(2)

    # if css newer than ccss
    if not os.path.exists(fn) and os.path.getmtime(fn) < os.path.getmtime(target):
        # do nothing
        return css_url

    src = file(fn)
    try:
        try:
            converted = convert(src.read())
        except (ParserError, EvalException), e:
            sys.stderr.write('Error in file %s: %s\n' % (fn, e))
            sys.exit(1)
        dst = file(target, 'w')
        try:
            dst.write(converted)
        finally:
            dst.close()
    finally:
        src.close()

    return css_url

