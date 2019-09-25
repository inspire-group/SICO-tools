#!/usr/bin/env python3


from scapy.all import *
from netfilterqueue import NetfilterQueue


responderIPs = set([])

potentialResponders = set([])
for ip in open("input.iplist"):
  ip = ip.strip()
  if ip == "":
    continue
  potentialResponders.add(ip)



def record(packet):
  #print packet
  pkt = IP(packet.get_payload()) #converts the raw packet to a scapy compatible string
  responderIP = str(pkt[IP].src)
  if responderIP in potentialResponders and responderIP not in responderIPs:
    responderIPs.add(responderIP)
    with open("responders.iplist", 'w') as f:
      f.write("\n".join(list(responderIPs)))
  print("{} Unique hosts. SYN ACK found from {}. ".format(len(responderIPs), responderIP))
  packet.accept() #accept the packet 



nfqueue = NetfilterQueue()
#1 is the iptabels rule queue number, modify is the callback function
nfqueue.bind(1, record) 
try:
  print("[*] waiting for data")
  nfqueue.run()
except KeyboardInterrupt:
  pass
