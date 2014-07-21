#!/usr/bin/env python

import sys

from nxfileremote import NXFileRemote

def message(msg):
    print("pyro test: " + str(msg))

if len(sys.argv) == 1:
    name = raw_input("Enter file name: ")
    uri = raw_input("Enter URI: ")
elif len(sys.argv) == 2:
    name = sys.argv.pop()
    uri = raw_input("Enter URI: ")
elif len(sys.argv) == 3:
    uri  = sys.argv.pop()
    name = sys.argv.pop()
else:
    print "usage: client.py <NAME> <URI>?"
    exit(1)

message("opening remote file: " + name + " on URI: " + uri)

with NXFileRemote(uri, name) as nxfr:
    # print("file: ") #  + str(nxfr._file))
    f = nxfr["/entry/data/v"]
    f[0,0,0]
    a = nxfr[("/entry/data/v",[0,0,0])]
    # a[0,0,0] # local
    t = nxfr[0,0,0] # remote
    message("entry: " + str(t))
