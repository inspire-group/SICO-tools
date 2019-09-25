ssh <YOUR_SERVER_HERE> -t 'bash -c "docker cp victim:/syn-sender/responders.iplist ~/results-from-syn-send/victim-responders.iplist; docker cp adversary:/syn-sender/responders.iplist ~/results-from-syn-send/adversary-responders.iplist;docker cp victim:/syn-sender/responders-ping.iplist ~/results-from-syn-send/victim-responders-ping.iplist; docker cp adversary:/syn-sender/responders-ping.iplist ~/results-from-syn-send/adversary-responders-ping.iplist"'




sftp <YOUR_SERVER_HERE> <<END
cd results-from-syn-send
get victim-responders.iplist
get adversary-responders.iplist
get victim-responders-ping.iplist
get adversary-responders-ping.iplist
END

python3 ./compare_responses.py victim-responders.iplist adversary-responders.iplist > results-syn.txt
python3 ./compare_responses.py victim-responders-ping.iplist adversary-responders-ping.iplist > results-ping.txt
python3 ./average_results.py results-syn.txt results-ping.txt > results-average.txt
