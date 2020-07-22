#!/bin/bash
for edge in $(ip netns list | awk '/edge/ {print $1}')
do
	ip netns del $edge
done
