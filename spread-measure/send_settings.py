
# Use ip a and get the mac address from the appropriate tunnel interface.
src_mac_addr = "aa:aa:aa:aa:aa:aa"


# Use the BIRD CLI to get an upstream router IP address. Then ping it. Then use ip n show to find the mac address.
dst_mac_addr = "aa:aa:aa:aa:aa:aa"


# Any src addr in the peering prefix space used for the experiment. 
src_ip_addr = "1.2.3.4"


# The interface of the peering mux that will send the packets.
out_interface = "tap1"

# The TCP port to send SYN packets to.
syn_port = 443
