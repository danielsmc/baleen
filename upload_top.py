#!/usr/bin/python

from generate_top import generate_top
import pystache
import sys

if len(sys.argv) < 2:
	print "pass an output filepath"
else:
	renderer = pystache.Renderer()

	data = generate_top()

	with open(sys.argv[1],"w") as fh:
		fh.write(renderer.render_path("template.mustache",data).encode('utf8'))