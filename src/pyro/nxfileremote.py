
import Pyro4

from nexpy.api.nexus import NXFile

class NXFileRemote(NXFile): 
    pass

nxremotefile = NXFileRemote("f.nxs")

daemon = Pyro4.Daemon()                 # make a Pyro daemon
uri=daemon.register(nxfileremote)   # register the greeting object as a Pyro object

print "NX remote file ready. Object uri =", uri      # print the uri so we can use it in the client later
daemon.requestLoop()                  # start the event loop of the server to wait for calls
