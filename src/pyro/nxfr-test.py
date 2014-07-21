#!/usr/bin/env python

import sys

from nxfileservice import NXFileService

def message(msg):
    print("pyro test: " + str(msg))

if len(sys.argv) != 3:
    print "usage: client.py <URI> <FILENAME>"
    exit(1)

uri = sys.argv[1]
name = sys.argv[2]
message("opening remote file: " + name)

with NXFileRemote(uri, name) as nxfr:
    print("file: ") #  + str(nxfr._file))
    f = nxfr["/entry/data/v"]
    f[0,0,0]
    a = nxfr[("/entry/data/v",[0,0,0])]
    # a[0,0,0] # local
    t = nxfr[0,0,0] # remote
    message("entry: " + str(t))
