#!/usr/bin/env python

import Pyro4
import sys
import threading
import time

import nexpy.api.nexus as nx
from nexpy.api.nexus import NXFile

def message(msg):
    print("pyro server: " + msg)

def shutdown():
    time.sleep(1)
    daemon.shutdown()

class NXFileRemote:
    name = ""
    nexusFile = None

    def initfile(self, name):
        message("Initializing NXFileRemote: " + name)
        self.name = name
        try: 
            self.nexusFile = NXFile(name, 'r')
        except Exception as e:
            message("Caught exception while opening: " + name)
            message("Exception message: " + str(e))
            return False
        return True
    
    def getitem(self, key):
        message("getitem")
        t = nx.load(self.name)
        message("t: " + str(t))
        return str(t[key])
    
    def tree(self):
        # return self.nexusFile.readfile()
        t = nx.load(self.name)
        # message("t: " + str(t))
        print "t.tree..."
        print "t.tree: " , str(t)
        return t
    
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
daemon = Pyro4.Daemon()
# Register the object as a Pyro object
uri = daemon.register(nxfileremote)

# Print the URI so we can use it in the client later
print("URI: "+str(uri))
sys.stdout.flush()

# Start the event loop of the server to wait for calls
daemon.requestLoop()
message("Daemon exited.")
