#!/usr/bin/env python

import Pyro4
import sys

from nexpy.api.nexus import NXFile

class NXFileRemote(NXFile):
    def initfile(self,name):
        print("Initializing NXFileRemote: " + name)
    def exit(self,code):
        print "Daemon exiting."
        def shutdown():
            daemon.shutdown()
        thread = threading.Thread(target=generate_symbols)
        thread.setDaemon(True)
        thread.start()



nxfileremote = NXFileRemote("f.nxs")

# Make an empty Pyro daemon
daemon = Pyro4.Daemon()
# Register the object as a Pyro object
uri = daemon.register(nxfileremote)

# Print the uri so we can use it in the client later
print("URI: "+str(uri))
sys.stdout.flush()

# Start the event loop of the server to wait for calls
daemon.requestLoop()
print("Daemon exited.")
