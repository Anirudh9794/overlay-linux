#!/bin/bash

set -e -o functrace

failure() {
    local lineno=$1
    local msg=$2
    echo "Failed at $lineno: $msg"
}
trap 'failure ${LINENO} "$BASH_COMMAND"' ERR

SUBNET_ID=""
VPC_ID=""
EDGE_MAX=""
BRIDGE_ADDR=""

while getopts 's:v:c:a:' c; do
    case $c in
    s) SUBNET_ID=$OPTARG ;;
    v) VPC_ID=$OPTARG ;;
    c) EDGE_MAX=$OPTARG ;;
    a) BRIDGE_ADDR=$OPTARG ;;
    esac
done

connect_by_veth() {
    PREFIX=$1
    V1="${PREFIX}0"
    V2="${PREFIX}1"
    NAMESPACE1=$2
    NAMESPACE2=$3
    IP1=$4
    IP2=$5

    ip link add ${V1} type veth peer name ${V2}
    ip link set ${V1} netns ${NAMESPACE1}
    ip link set ${V2} netns ${NAMESPACE2}
    ip netns exec ${NAMESPACE1} ip link set ${V1} up
    ip netns exec ${NAMESPACE2} ip link set ${V2} up

    ip netns exec ${NAMESPACE1} ip addr add ${IP1} dev ${V1}
    ip netns exec ${NAMESPACE2} ip addr add ${IP2} dev ${V2}
}

# ip netns add S${SUBNET_ID}V${VPC_ID}
# Now, run them as containers
CONTAINER_NAME="S${SUBNET_ID}V${VPC_ID}"
docker run -v /home/ece792/bgp/transit.conf:/etc/quagga/bgpd.conf -v /home/ece792/bgp/daemons:/etc/quagga/daemons --privileged --name $CONTAINER_NAME \
    -d -ti anir9794/quagga_docker

# Expose their namespaces
id=$(docker inspect -f '{{.State.Pid}}' $CONTAINER_NAME)
ln -sf /proc/$id/ns/net /var/run/netns/$CONTAINER_NAME

for e in $(seq 0 $EDGE_MAX); do
    O_1=$((e * 2 + 1))
    O_2=$((e * 2 + 2))
    connect_by_veth s${SUBNET_ID}v${VPC_ID}e${e} S${SUBNET_ID}V${VPC_ID} \
        V${VPC_ID}E${e} 1.${VPC_ID}.${SUBNET_ID}.${O_1}/24 1.${VPC_ID}.${SUBNET_ID}.${O_2}/24
    if [ ! -z "BRIDGE_ADDR"]; then
        ip netns exec V${VPC_ID}E${e} ip route add "$BRIDGE_ADDR" dev s${SUBNET_ID}v${VPC_ID}e${e}1 || true
    fi
done

ip netns exec S${SUBNET_ID}V${VPC_ID} ip route | grep 'default' &&
    ip netns exec S${SUBNET_ID}V${VPC_ID} ip route del default
# Adding default route to the '0' edge
ip netns exec S${SUBNET_ID}V${VPC_ID} ip route add default via 1.${VPC_ID}.${SUBNET_ID}.2

# Create a bridge
ip netns exec S${SUBNET_ID}V${VPC_ID} brctl addbr br
ip netns exec S${SUBNET_ID}V${VPC_ID} ip link set dev br up

# Add ip address to the bridge if provided
if [ ! -z "$BRIDGE_ADDR" ]; then
    ip netns exec S${SUBNET_ID}V${VPC_ID} ip addr add ${BRIDGE_ADDR} dev br
fi
