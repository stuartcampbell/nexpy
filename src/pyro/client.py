#!/usr/bin/env python

"""
Dummy client for prototyping NexPyro
"""

import sys
import Pyro4

def message(msg):
    print("client: " + str(msg))

if len(sys.argv) != 3:
    print "usage: client.py <URI> <FILENAME>"
    exit(1)

uri = sys.argv[1]
# raw_input("What is the Pyro uri of the service? ").strip()
name = sys.argv[2]
# raw_input("What is the file name? ").strip()
message("opening remote file: " + name)

# Get a Pyro proxy to the remote object
fileremote = Pyro4.Proxy(uri)

# Use proxy object normally
message(fileremote)
try:
    b = fileremote.initfile(name)
except Exception as e:
    print "Caught exception during remote file operations!"
    print("Exception message: " + str(e))
    
fileremote.exit(0)
if b:
    message("Success.")
else: 
    message("Failed!")
    exit(1)
exit(0)
