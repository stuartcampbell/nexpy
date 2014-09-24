#!/usr/bin/env python

"""
Daemon process presenting NeXus file over Pyro
"""


import Pyro4
import sys
import threading
import time

import nexpy.api.nexus as nx
from nexpy.api.nexus import NXFile

def msg(msg):
    print("pyro server: " + msg)

def msgv(m, v):
    msg(m + ": " + str(v))

def shutdown():
    time.sleep(1)
    daemon.shutdown()

class NXFileService:
    name = ""
    nexusFile = None
    root = None
    path = None

    def initfile(self, name):
        msg("Initializing NXFileService: " + name)
        self.name = name
        try:
            msgv("opening", name)
            self.nexusFile = NXFile(name, 'r')
            self.root = nx.load(self.name, close=False)
            self.root._proxy = True
            nx.setserver(True) 
        except Exception as e:
            msg("Caught exception while opening: " + name)
            msg("Exception msg: " + str(e))
            return False
        return True

    # We cannot expose __getitem__ via Pyro
    # Cf. pyro-core mailing list, 7/20/2014
    
    def getitem(self, key):
        msgv("getitem", key)
        result = self.root[key]
        msgv("result", result)
        return result
    
    # Two-step call sequence
    def getdata(self, key):
        msgv("getdata", key)
        try:
            msg("get path: " + str(self.path))
            if self.path == None:
                self.path = key
                msg("ok")
                t = self.root[self.path]
                msg("returning t")
            else:
                g = self.root[self.path]
                print("g: " + str(g))
                t = g[key]
                self.path = None
            msg("set path: " + str(self.path))
        except Exception as e:
            print("EXCEPTION in getitem(): " + str(e))
            t = None
        msg("getitem result: " + str(t))
        return t

    def tree(self):
        print("tree...")
        print "tree root: " , str(self.root)
        return self.root

    def filename(self):
        return self.nexusFile.filename()

    def getentries(self):
        print(self.nexusFile.getentries())
        return True

    def exit(self,code):
        msg("Daemon exiting...")
        thread = threading.Thread(target=shutdown)
        thread.setDaemon(True)
        thread.start()

nxfileservice = NXFileService()

# Make an empty Pyro daemon
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
daemon = Pyro4.Daemon()
# Register the object as a Pyro object
uri = daemon.register(nxfileservice)

# Print the URI so we can use it in the client later
print("URI: " + str(uri))
sys.stdout.flush()

# Start the event loop of the server to wait for calls
daemon.requestLoop()
msg("Daemon exited.")
