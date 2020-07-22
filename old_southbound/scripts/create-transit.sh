#!/bin/bash

set -e

TRANSIT="transit"
EX_TRANSIT="ip netns exec $TRANSIT"
TRANSIT_SUBNET="3.3.50.0/24"

ip netns list | grep $TRANSIT || \
	ip netns add $TRANSIT
	
ip link add tr0 type veth peer name tr1
ip link set tr0 netns $TRANSIT

ip netns exec $TRANSIT ip link set tr0 up
ip link set tr1 up

ip netns exec $TRANSIT ip addr add 3.3.50.1/24 dev tr0
ip addr add 3.3.50.2/24 dev tr1

# ipttables
#$EXTRANSIT iptables -t nat -A POSTROUTING -o tr0 -j MASQUERADE
#iptables -t nat -s  -s $TRANSIT_SUBNET ! -d $TRANSIT_SUBNET -j MASQUERADE

# create tunnel from provider1 namespaces
ip netns exec $TRANSIT ip link add prov1 type gretap local 3.3.50.1 remote 3.3.1.1
ip netns exec $TRANSIT ip link set prov1 up

# create tunnel from provider namespace
ip netns exec $TRANSIT ip link add prov2 type gretap local 3.3.50.1 remote 3.3.2.1
ip netns exec $TRANSIT ip link set prov2 up

# TODO add ip routes to gretunnel
