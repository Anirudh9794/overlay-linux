#!/bin/bash

# NOT TESTED

set -e -o functrace

failure() {
    local lineno=$1
    local msg=$2
    echo "Failed at $lineno: $msg"
}
trap 'failure ${LINENO} "$BASH_COMMAND"' ERR

VPC_ID=""
SCALE_FACTOR=""
TRANSIT_ID=""
RELIABILITY_FACTOR=""

while getopts 'v:s:t:r:' c; do
    case $c in
    v) VPC_ID=$OPTARG ;;
    s) SCALE_FACTOR=$OPTARG ;;
    t) TRANSIT_ID=$OPTARG ;;
    r) RELIABILITY_FACTOR=$OPTARG ;;
    esac
done

create_vxlan_tunnel() {
    TUNNEL_NAME=$1
    TRANSIT_ID_TMP=$2
    EXIT_INTERFACE=$3
    REMOTE_IP=$4
    NAMESPACE=$5
    BRIDGE_NAME="vbr-$TUNNEL_NAME"
    VPC_ID_TMP=$6

    ip netns exec $NAMESPACE brctl addbr $BRIDGE_NAME
    ip netns exec $NAMESPACE ip link set $BRIDGE_NAME up
    ip netns exec $NAMESPACE ip addr add 5.5.5.${TRANSIT_ID_TMP}/24 dev $BRIDGE_NAME

    ip netns exec $NAMESPACE ip link add $TUNNEL_NAME type vxlan id $VPC_ID_TMP dev $EXIT_INTERFACE dstport 4789
    ip netns exec $NAMESPACE ip link set $TUNNEL_NAME up
    ip netns exec $NAMESPACE brctl addif $BRIDGE_NAME $TUNNEL_NAME
    ip netns exec $NAMESPACE bridge fdb append 00:00:00:00:00:00 dev $TUNNEL_NAME dst $REMOTE_IP
    
    # ip netns exec $NAMESPACE ip tunnel add $TUNNEL_NAME mode gre local $LOCAL_IP remote $REMOTE_IP
    # ip netns exec $NAMESPACE ip link set $TUNNEL_NAME up

    # adding routes??
    docker exec $NAMESPACE service quagga restart
}

EDGE_MAX=$((SCALE_FACTOR - 1))
TRANSIT_MAX=$((RELIABILITY_FACTOR - 1))

for i in $(seq 0 $EDGE_MAX); do
    for j in $(seq 0 $TRANSIT_MAX); do
        create_vxlan_tunnel "tr${TRANSIT_ID}$j" "$TRANSIT_ID" "v${VPC_ID}e${i}0" "7.$TRANSIT_ID.$j.1" "V${VPC_ID}E${i}" "${VPC_ID}${j}${i}"
    done
    # TODO remove this 
    # ip netns exec "V${VPC_ID}E${i}" ip route add 1.0.0.0/8 dev "vbr-t$TRANSIT_ID"
done

