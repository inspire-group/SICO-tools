This directory contains code for our viable AS estimation. It is in viable_as_estimation.py.

viable_as_estimation.py requires 3 input files:

topology_file: 20190301.as-rel2.txt
This must be a CAIDA format AS relationship databse. Data from March 2019 is included in the file 20190301.as-rel2.txt. Data from other months can be downloaded from: http://www.caida.org/data/as-relationships/

as_forward: as_forward.csv
This is a list of ANSs for all ASes seen forwarding communities.

as_full_support: as_full_support.csv
This is a list of ASNs for all ASes that have full support for the BGP communities outlined in the paper. We found these ASes via manual inspection of routing policy as described in the paper.

Alternate file names can be spcified with optional command line arguments. Run ./viable_as_estimation.py -h for command line usage help.


To run the program, run:
./viable_as_estimation.py


Output:
This program outputs multiple statistics about the input topology. The outputs used to generate the percentages in the paper were:

The total number of ASes in the topology:
%d ASes found in topology 64167


The fraction of multi-homed ASes:
%d multi homed ASes 37142


Multi-homed ASes with a direct provider that fully supports communities:
%d multi homed ASes with a provider with full commuinty support 15357


Multi-homed ASes with either a provier that supports communities, or a way to forward communities to a provider that does. This also excludes ASes that can forward communities but have their providers peer in such a way that they will still not be able to maintain a valid route:
%d multi homed ASes with a forwarding path to full community support 30927


