#!/usr/bin/python

import os
import time

print "starting..."
while True:
	os.system("python -u collect.py")
	print "looks like we crashed. restarting."
	time.sleep(1)
