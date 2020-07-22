#!/bin/bash
set -e
NAME=""
LOCAL=""
REMOTE=""
ROUTE=""
PROVIDER_NS=""

while getopts 'n:l:r:p:' c
do
  case $c in
    n) NAME=$OPTARG ;;
    l) LOCAL=$OPTARG ;;
    r) REMOTE=$OPTARG ;;
    #f) ROUTE=$OPTARG ;;
    p) PROVIDER_NS=$OPTARG ;;
  esac
done

if [ -z "$NAME" ] | [ -z "$LOCAL" ] | [ -z "$REMOTE" ]
then
	echo "usage is invalid"
	exit 1
fi

ip netns exec $PROVIDER_NS ip tunnel add $NAME mode gre local $LOCAL remote $REMOTE
ip netns exec $PROVIDER_NS ip link set dev $NAME up
