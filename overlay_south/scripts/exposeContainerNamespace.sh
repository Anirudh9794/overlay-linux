#!/bin/bash

CONTAINER_NAME=$1

# Expose their namespaces
id=$(docker inspect -f '{{.State.Pid}}' $CONTAINER_NAME)
ln -sf /proc/$id/ns/net /var/run/netns/$CONTAINER_NAME
