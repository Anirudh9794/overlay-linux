#!/bin/bash
set -e

#if [ -z "$(ip netns list | awk '/provider/')" ]
#then
ip netns list | grep 'provider' || \
	(ip netns add provider && \
	ip link add p0 type veth peer name p1 && \
	ip link set p0 netns provider && \
	ip netns exec provider ip link set p0 up && \
	ip link set p1 up && \
	# add ip addresses 
	ip netns exec provider ip addr add 3.3.$1.1/24 dev p0 && \
	ip netns exec provider ip route add default via 3.3.$1.2 && \
	ip addr add 3.3.$1.2/24 dev p1 && \
	# add iptable rules to the provider namespace
	ip netns exec provider iptables -t nat -A POSTROUTING -o p0 -j MASQUERADE && \
	iptables -t nat -A POSTROUTING -s 3.3.$1.0/24 ! -d 3.3.$1.0/24 -j MASQUERADE)
#fi	
