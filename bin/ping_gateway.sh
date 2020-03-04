#! /usr/bin/env bash
# ping_gateway.sh
# ping the gateway host

failures=0
trap 'failures=$((failures+1))' ERR

HOST=${1}
TIMEOUT=${2:-1}

/bin/ping -c1 -w$TIMEOUT $HOST > /dev/null 2>&1

if ((failures == 0)); then
        echo "Success"
else
	echo "Failure"
	exit 1
fi
