import scapy.all as sca
import time
import thread
import threading
import signal
import sys
import copy
from matplotlib import pyplot as plt
from matplotlib import rcParams
import math

# needed to gracefully exit all threads
stopEvent = threading.Event() 
def signal_handler(signal, frame):
  global stopEvent
  print("Ctrl+C captured, exiting program!")
  stopEvent.set()
  time.sleep(1.0)
  sys.exit()
signal.signal(signal.SIGINT, signal_handler)

class ScapyRssi:
  def __init__(self, interface):
    self.data = {}
    self.interface = interface
    self.dataMutex = thread.allocate_lock()
    self.time0 = time.time()
    thread.start_new_thread(self.sniff, (stopEvent,))
  def sniff(self, stopEvent):
    while not stopEvent.is_set():
      packets = sca.sniff(iface=self.interface, count = 100)
      for pkt in packets:
        addr, rssi = self.parsePacket(pkt)
        if addr is not None:
          with self.dataMutex:
            if addr in self.data.keys():
              self.data[addr].append(rssi)
            else:
              self.data[addr] = [rssi]
  def parsePacket(self, pkt):
    if pkt.haslayer(sca.Dot11) :
      if pkt.addr2 != None:
        return pkt.addr2, -(256-ord(pkt.notdecoded[-4:-3]))
    return None, None
  def plot(self, num):
    plt.clf()
    rcParams["font.family"] = "serif"
    rcParams["xtick.labelsize"] = 8
    rcParams["ytick.labelsize"] = 8
    rcParams["axes.labelsize"] = 8
    rcParams["axes.titlesize"] = 8
    data = {}
    time1 = time.time()
    with self.dataMutex:
      data = copy.deepcopy(self.data)
    nodes = [x[0] for x in sorted([(addr, len(data[addr])) for addr in data.keys()], key=lambda x:x[1], reverse=True)]
    nplots = min(len(nodes), num)
    for i in range(nplots):
      plt.subplot(nplots, 1, i+1)
      plt.title(str(nodes[i]) + ": " + str(len(data[nodes[i]])) + " packets @ " + "{0:.2f}".format(len(data[nodes[i]])/(time1-self.time0)) + " packets/sec")
      plt.hist(data[nodes[i]], range=(-100, -20), bins=80)
      plt.gca().set_xlim((-100, -20))
    plt.gcf().set_size_inches((6, 4*nplots))
    plt.savefig("hists.pdf")

if __name__ == "__main__":
  sniffer = ScapyRssi("wlan0")
  time.sleep(300)
  sniffer.plot(20)
  print "plotted"