#!/usr/bin/env python

import Pyro4
import sys
import threading
import time

import nexpy.api.nexus as nx
from nexpy.api.nexus import NXFile

from numpy import array

def message(msg):
    print("pyro server: " + msg)

def shutdown():
    time.sleep(1)
    daemon.shutdown()

class NXFileRemote:
    name = ""
    nexusFile = None
    root = None

    def initfile(self, name):
        message("Initializing NXFileRemote: " + name)
        self.name = name
        try:
            self.nexusFile = NXFile(name, 'r')
            self.root = nx.load(self.name)
        except Exception as e:
            message("Caught exception while opening: " + name)
            message("Exception message: " + str(e))
            return False
        return True

    def getitem(self, path, key):
        # have self.root
        message("getitem inputs: " + str(path) + " " + str(key))
        t = self.root[path][key]
        message("getitem result: " + str(t))
        return t

    # def __getitem__(self, key):
    #     # have self.root
    #     print ("__getitem__: " + key)

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
        message("Daemon exiting...")
        thread = threading.Thread(target=shutdown)
        thread.setDaemon(True)
        thread.start()

nxfileremote = NXFileRemote()

# Make an empty Pyro daemon
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
daemon = Pyro4.Daemon()
# Register the object as a Pyro object
uri = daemon.register(nxfileremote)

# Print the URI so we can use it in the client later
print("URI: " + str(uri))
sys.stdout.flush()

# Start the event loop of the server to wait for calls
daemon.requestLoop()
message("Daemon exited.")
