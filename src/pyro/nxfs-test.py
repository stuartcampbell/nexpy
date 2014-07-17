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

with NXFileRemote(uri, name) as nxfs:
    print("file: ") #  + str(nxfs._file))
    f = nxfs["/entry/data/v"]
    f[0,0,0]
    a = nxfs[("/entry/data/v",[0,0,0])]
    # a[0,0,0] # local
    t = nxfs[0,0,0] # remote
    message("entry: " + str(t))
