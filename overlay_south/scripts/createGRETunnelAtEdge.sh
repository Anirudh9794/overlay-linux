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

create_gre_tunnel() {
    TUNNEL_NAME=$1
    LOCAL_IP=$2
    REMOTE_IP=$3
    NAMESPACE=$4
    TUNNEL_IP=$5

    ip netns exec $NAMESPACE ip tunnel add $TUNNEL_NAME mode gre local $LOCAL_IP remote $REMOTE_IP
    ip netns exec $NAMESPACE ip link set $TUNNEL_NAME up

    # Add ip address to the tunnel interface
    ip netns exec $NAMESPACE ip addr add $TRANSIT_IP dev $TUNNEL_NAME 

    # bgpd and zebra restart
    docker exec $NAMESPACE service quagga restart
}

EDGE_MAX=$((SCALE_FACTOR - 1))
TRANSIT_MAX=$((RELIABILITY_FACTOR - 1))

for i in $(seq 0 $EDGE_MAX); do
    for j in $(seq 0 $TRANSIT_MAX); do
        create_gre_tunnel "tr${TRANSIT_ID}$j" "2.$VPC_ID.$i.1" "7.$TRANSIT_ID.$j.1" "V${VPC_ID}E${i}" "9.$i.$j.10/24"
    done
done

