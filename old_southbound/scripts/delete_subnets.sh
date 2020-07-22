#!/bin/bash
for subnet in $(ip netns list | awk '/subnet/ {print $1}')
do
	ip netns del $subnet
done
