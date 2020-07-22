#!/bin/bash
set -e
ip netns del provider
# TODO delete iptalbe rules in host
