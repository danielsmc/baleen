#!/usr/bin/python

from generate_top import generate_top
import pystache

renderer = pystache.Renderer()

data = generate_top()

with open("web/index.html","w") as fh:
	fh.write(renderer.render_path("template.mustache",data).encode('utf8'))