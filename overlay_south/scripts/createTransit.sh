#!/bin/bash

set -e -o functrace

failure() {
    local lineno=$1
    local msg=$2
    echo "Failed at $lineno: $msg"
}
trap 'failure ${LINENO} "$BASH_COMMAND"' ERR

RELIABLITY_FACTOR=""
TRANSIT_ID=""

while getopts 'r:i:' c; do
    case $c in
    r) RELIABLITY_FACTOR=$OPTARG ;;
    i) TRANSIT_ID=$OPTARG ;;
    esac
done

if
    [ -z "$RELIABLITY_FACTOR" ] &
    [ -z "$TRANSIT_ID" ]
then
    echo "Usage is incorrect"
    echo "usage: sudo bash createTransit.sh -r [RELIABILITY_FACTOR] -i [TRANSIT_ID]"
    exit 1
fi

create_external_namespace() {
    NAME=$1
    PREFIX=$2
    L1="${PREFIX}0"
    L2="${PREFIX}1"
    L1_IP=$3
    L2_IP=$4
    GATEWAY=$5
    CIDR=$6
    BGP_CONF_FILE=$7

    # ip netns add $NAME
    docker run -v /home/ece792/bgp/$BGP_CONF_FILE:/etc/quagga/bgpd.conf -v /home/ece792/bgp/daemons:/etc/quagga/daemons --privileged --name $NAME \
        -d -ti anir9794/quagga_docker

    # Expose their namespaces
    id=$(docker inspect -f '{{.State.Pid}}' $NAME)
    ln -sf /proc/$id/ns/net /var/run/netns/$NAME

    ip link add ${L1} type veth peer name ${L2}
    ip link set ${L1} netns ${NAME}
    ip netns exec ${NAME} ip link set ${L1} up
    ip link set ${L2} up

    ip netns exec ${NAME} ip addr add ${L1_IP} dev ${L1}
    ip addr add ${L2_IP} dev ${L2}

    ip netns exec $NAME ip route | grep 'default' && \
        ip netns exec $NAME ip route del default

    ip netns exec ${NAME} ip route add default via ${GATEWAY}

    # ip netns exec ${NAME} iptables -t nat -A POSTROUTING -o ${L1} -j MASQUERADE
    # (iptables -t nat -S | grep "-A POSTROUTING -s ${CIDR} ! -d ${CIDR} -j MASQUERADE") ||
    #     iptables -t nat -A POSTROUTING -s ${CIDR} ! -d ${CIDR} -j MASQUERADE
}

COUNT_MAX=$((RELIABLITY_FACTOR - 1))

for e in $(seq 0 $COUNT_MAX); do
    BGP_CONF_FILE="ready/transit-${TRANSIT_ID}-${e}.conf"
    create_external_namespace transit${TRANSIT_ID}-${e} t${TRANSIT_ID}${e} \
        7.${TRANSIT_ID}.${e}.1/24 7.${TRANSIT_ID}.${e}.2/24 7.${TRANSIT_ID}.${e}.2 7.${TRANSIT_ID}.${e}.0/24 $BGP_CONF_FILE
done
