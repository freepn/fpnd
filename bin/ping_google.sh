#! /usr/bin/env bash
# ping_google.sh
# ping the google dns

failures=0
trap 'failures=$((failures+1))' ERR

IFACE=${1:-eth0}
TIMEOUT=${2:-1}

/bin/ping -c1 -w$TIMEOUT -I$IFACE 8.8.8.8 > /dev/null 2>&1

if ((failures == 0)); then
        echo "Success"
else
	echo "Failure"
	exit 1
fi
