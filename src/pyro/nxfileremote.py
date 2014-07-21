
"""
NXFileRemote
The wrapper class representing a remote NX file
Contains a Pyro proxy
"""

import sys
import Pyro4

import nexpy.api.nexus as nx
from nexpy.api.nexus import NXFile

import numpy as np

def message(msg):
    print("pyro client: " + str(msg))

class NXFileRemote(NXFile):

    def __init__(self, uri, name):
        # Get a Pyro proxy to the remote object
        Pyro4.config.SERIALIZER = "pickle"
        self._file = Pyro4.Proxy(uri)
        b = self._file.initfile(name)
        assert(b)

    def __getitem__(self, key):
        return self._file.getitem(key)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._file.exit(0)
