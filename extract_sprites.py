#!/usr/bin/env python
"""Extract the names of the sprites of each sprite map in a CleverCSS."""

import sys
import clevercss

# This is *a little* ugly, but ISTM there are no really great solutions here.
# Pick your poision, sort of.
clevercss.Parser.sprite_map_cls = clevercss.AnnotatingSpriteMap

# Run the file through the parser so the annotater catches it all.
fname = sys.argv[1]
clevercss.convert(open(fname, "U").read(), fname=fname)

# Then extract the sprite names. Should probably add output options here.
for smap, sprites in clevercss.AnnotatingSpriteMap.all_used_sprites():
    map_name = smap.map_fname.to_string(None)
    sprite_names = " ".join(s.name for s in sprites)
    print "%s: %s" % (map_name, sprite_names)

