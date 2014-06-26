#!/usr/bin/env python

"""
Dummy client for prototyping NexPyro
"""

import sys
import Pyro4

if len(sys.argv) != 3:
    print "usage: client.py <URI> <FILENAME>"
    exit(1)

uri = sys.argv[1]
# raw_input("What is the Pyro uri of the service? ").strip()
name = sys.argv[2]
# raw_input("What is the file name? ").strip()
print("opening remote file: " + name)

# Get a Pyro proxy to the remote object
fileremote = Pyro4.Proxy(uri)

# Use proxy object normally
print fileremote
fileremote.initfile(name)
fileremote.exit(0)
