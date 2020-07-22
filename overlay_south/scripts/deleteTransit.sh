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
    echo "usage: sudo bash deleteTransit.sh -r [RELIABILITY_FACTOR] -i [TRANSIT_ID]"
    exit 1
fi

COUNT_MAX=$((RELIABLITY_FACTOR - 1))

for e in $(seq 0 $COUNT_MAX); do
    ip netns del transit${TRANSIT_ID}-${e} || true
    # remove docker container
    docker rm -f transit${TRANSIT_ID}-${e} || true
    # iptables -t nat -D POSTROUTING -s 7.${TRANSIT_ID}.${e}.0/24 ! -d 7.${TRANSIT_ID}.${e}.0/24 -j MASQUERADE || true
done

