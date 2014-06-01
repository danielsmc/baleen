#!/usr/bin/python

from generate_top import generate_top
import os
import pystache
import stat
import sys
import tempfile

if len(sys.argv) < 2:
	print "pass an output filepath"
else:
	renderer = pystache.Renderer()

	data = generate_top()

	temp_fd,temp_path = tempfile.mkstemp()
	with os.fdopen(temp_fd,'w') as fh:
		fh.write(renderer.render_path("template.mustache",data).encode('utf8'))

	os.chmod(temp_path,stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
	os.rename(temp_path,sys.argv[1])