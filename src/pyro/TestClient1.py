#!/usr/bin/env python

"""
Dummy client for prototyping NexPyro
"""

import sys
import Pyro4

def message(msg):
    print("pyro client: " + str(msg))

if len(sys.argv) != 2:
    print "usage: client.py <URI>"
    exit(1)

uri = sys.argv[1]

# Get a Pyro proxy to the remote object
Pyro4.config.SERIALIZER = "pickle"
proxy = Pyro4.Proxy(uri)
b = True

# Use proxy object normally
try:
    b = proxy.f1("hello")
    pass
except Exception as e:
    print "Caught exception during remote operations!"
    print("Exception message: " + str(e))
    print "Pyro remote traceback:"
    print "".join(Pyro4.util.getPyroTraceback())

message("Shutting down service...")
proxy.exit(0)
if b:
    message("Success.")
else:
    message("Failed!")
    exit(1)
exit(0)
