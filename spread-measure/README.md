This folder contains the tools to measure spread by sending SYN and PING packets. It contains both scripts to be run on remote machines connected to peering nodes and data processing scripts that are independent of the peering nodes.


Part one: sending/recording pings and SYNs:

Requirements:
pip install NetfilterQueue
scapy (already included)

Note: We use a local version of scapy that is copied in this git repository due to issues with the package manager version being out of date.



Required files:
input.iplist
input-ping.iplist

input.iplist is a list of hosts that will be sent TCP SYN packets to port 443.
input-ping.iplist is a list of hosts that will be sent ICMP PING packets.

Both of these files are empty and need to be populated with the sample host IP addresses being studied.

Note: These files must be present on both the sending AND receiving machines. The PING and SYN recording scripts filter results to only include results from the hosts in the input files. 


To properly measure spread as computed in our paper, 2 separate servers (or virtual machines) are needed: one to serve as the victim and one as the adversary. Both servers must be listening on the same IP address. We used docker containers labeled victim and adversary (that were attached via separate VPNs to different ASes and Internet exchanges). 

Of these two machines, one must be used to send SYN or PING packets and both machines must simultaneously be configured to receive SYN or PING packets. In theory the sending machine does not have to be either the victim or adversary machine, but this can cause sent packets to be filtered because of IP spoofing (the sending script uses the IP address of the victim and adversary as the source IP address).

To listen for packets on a machine:

# Tell IPtables to queue received PING and SYN packets for processing by the scripts.
./iptables-command.sh

# Listen for PING packets. This script is blocking and will occupy the terminal. Use CTR+C to cancel when done. Results are saved in real time so no data is lost by canceling.
./record_ping.py

# Listen for SYN packets. Operates similarly to record_ping.py.
./record_syn_ack.py

# Undo the filtering action in IP tables. Note that if you do not remove the IP tables commands your host will not be able to receive echo-response or TCP SYN@443 packets.
./undo-iptables.sh


The above procedure generates results.iplist and results-ping.iplist. Each is a list of hosts that were in the input file and were found sending responses while the program was running. These files are overwritten on consecutive program runs so be sure to back them up.

Send packets:
# Edit the send settings file. With the appropriate values as per the instructions.
vim send_settings.py

# Be sure the victim and adversary server are listening for SYN packets. Then send them.
./send_syn.py

# Repeat with PING.
./send_ping.py



Part two: remote results processing.

The results from the above runs must be compared. Included is read-results-remote.sh: an example script to read data from two remote docker containers serving as the victim and the adversary. To use it, the host IP must be specified. Also, the folders in the docker containers must be in the appropriate paths.

This script also calls compare_responses.py and average_results.py which compare the two results files to calculate spread SYN, spread PING and spread average.
