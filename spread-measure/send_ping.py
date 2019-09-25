#!/usr/bin/env python3


from scapy.all import *
import send_settings

inputFile = "input-ping.iplist"

numHosts = sum(1 if line.strip() != "" else 0 for line in open(inputFile))

sentHosts = 0
for ip in open(inputFile):
  ip = ip.strip()
  if ip == "":
    continue

  print("Sent to {} of {} hosts. Now sending to: {}".format(sentHosts, numHosts, ip))
  sentHosts += 1
  sendp(Ether(src=send_settings.src_mac_addr, dst=send_settings.dst_mac_addr) / IP(src=send_settings.src_ip_addr, dst=ip) / ICMP(), iface=send_settings.out_interface)
  #send(IP(dst=ip) / ICMP())
