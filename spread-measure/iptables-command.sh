iptables -I INPUT -p tcp --tcp-flags SYN,ACK SYN,ACK -j NFQUEUE --queue-num 1

iptables -I INPUT -p icmp --icmp-type echo-reply -j NFQUEUE --queue-num 2

#iptables -D INPUT -p tcp --tcp-flags SYN,ACK SYN,ACK -j NFQUEUE --queue-num 1

#iptables -D INPUT -p icmp --icmp-type echo-reply -j NFQUEUE --queue-num 2