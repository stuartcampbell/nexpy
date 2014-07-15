#!/usr/bin/env python

"""
Dummy client for prototyping NexPyro
"""

import sys
import Pyro4

def message(msg):
    print("pyro client: " + str(msg))

if len(sys.argv) != 3:
    print "usage: client.py <URI> <FILENAME>"
    exit(1)

uri = sys.argv[1]
# raw_input("What is the Pyro uri of the service? ").strip()
name = sys.argv[2]
# raw_input("What is the file name? ").strip()
message("opening remote file: " + name)

# Get a Pyro proxy to the remote object
Pyro4.config.SERIALIZER = "pickle"
fileremote = Pyro4.Proxy(uri)
b = True

# Use proxy object normally
try:
    b = fileremote.initfile(name)
    # n = fileremote.filename()
    t = fileremote.tree()
    message("t: " + str(t))
    message("nxname: " + t.nxname)
    message("tree: " + t.tree)
    message("data: " + str(t.entry.data.signal.nxdata))
    message("data: " + str(t.entry.data["signal"]))
    message("entry: " + fileremote.getitem("entry"))
    # print("name="+n)
    pass
except Exception as e:
    print "Caught exception during remote file operations!"
    print("Exception message: " + str(e))
    b = False

message("Shutting down service...")
fileremote.exit(0)
if b:
    message("Success.")
else:
    message("Failed!")
    exit(1)
exit(0)
