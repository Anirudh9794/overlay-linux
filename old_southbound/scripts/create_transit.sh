#!/bin/bash

set -e

TRANSIT="transit"
EX_TRANSIT="ip netns exec $TRANSIT"
TRANSIT_SUBNET="3.3.50.0/24"
HOST1=""
HOST2=""
TR=""

while getopts 'a:b:' c
do
  case $c in
    a) HOST1=$OPTARG ;;
    b) HOST2=$OPTARG ;;
  esac
done

ip netns list | grep $TRANSIT || \
	ip netns add $TRANSIT
	
ip link add tr0 type veth peer name tr1
ip link set tr0 netns $TRANSIT

ip netns exec $TRANSIT ip link set tr0 up
ip link set tr1 up

ip netns exec $TRANSIT ip addr add 3.3.50.1/24 dev tr0
ip addr add 3.3.50.2/24 dev tr1
ip netns exec $TRANSIT ip route add default via 3.3.50.2

# ipttables
#$EXTRANSIT iptables -t nat -A POSTROUTING -o tr0 -j MASQUERADE
#iptables -t nat -s  -s $TRANSIT_SUBNET ! -d $TRANSIT_SUBNET -j MASQUERADE

ip netns exec $TRANSIT ip tunnel add prov1 mode gre local 3.3.50.1 remote 3.3.$HOST1.1
ip netns exec $TRANSIT ip link set dev prov1 up

ip netns exec $TRANSIT ip tunnel add prov2 mode gre local 3.3.50.1 remote 3.3.$HOST2.1
ip netns exec $TRANSIT ip link set dev prov2 up

