#!/bin/bash

set -e

NAME=""   # name of vxlan
PLACE=""  # subnet[vpc]-[subnet]
INTERFACE=""
REMOTE="" # 1.vpc.subnet.1
BRIDGE=""
LOCAL_EDGE_NS=""
REMOTE_EDGE=""

while getopts 'n:i:r:p:b:e:' c
do
  case $c in
    n) NAME=$OPTARG ;;
    i) INTERFACE=$OPTARG ;;
    #l) LOCAL=$OPTARG ;;
    r) REMOTE=$OPTARG ;;
    #f) ROUTE=$OPTARG ;;
    p) PLACE=$OPTARG ;;
    b) BRIDGE=$OPTARG ;;
    e) LOCAL_EDGE_NS=$OPTARG ;;
  esac
done

# TODO check if all paramters are set
if [ -z $NAME ] | [ -z $INTERFACE ] | [ -z $REMOTE ] | [ -z $PLACE ] | [ -z $BRIDGE ] | [ -z $LOCAL_EDGE_NS ]
then
	echo "Usage is incorrect"
	exit 1
fi

ip netns exec $PLACE ip link add $NAME type vxlan id 42 dev $INTERFACE dstport 4789
ip netns exec $PLACE ip link set $NAME up
ip netns exec $PLACE brctl addif $BRIDGE $NAME

ip netns exec $PLACE bridge fdb append to 00:00:00:00:00:00 dst $REMOTE dev $NAME

REMOTE_EDGE="$(echo $REMOTE | cut -d'.' -f2)"

ip netns exec $LOCAL_EDGE_NS ip route add $REMOTE dev tun$REMOTE_EDGE
