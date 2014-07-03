#!/usr/bin/env python

import Pyro4
import sys
import threading

from nexpy.api.nexus import NXFile

def message(msg):
    print("pyro server: " + msg)

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
         
    def getentries(self):
        pass 
    
    def exit(self,code):
        print "Daemon exiting..."
        def shutdown():
            daemon.shutdown()
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
print("Daemon exited.")
