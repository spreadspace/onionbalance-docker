#!/bin/sh -e

# Exit if either subprocess terminates
trap 'exit' CHLD

/usr/bin/tor -f /torrc --RunAsDaemon 0 &
/k8sbalance.py &
