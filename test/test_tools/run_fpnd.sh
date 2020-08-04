#! /bin/sh
#
# this runs fpnd on each gentoo host with short delay in between
# use "stop" arg to overide start

failures=0
trap 'failures=$((failures+1))' ERR

CMD_ARG=${1:-start}

INFRA_HOSTS="infra-01 infra-02 exit-01"
# node-05 node-01
GEN_HOSTS="node-01 node-02 node-03 node-04 node-05"
ALL_HOSTS="${INFRA_HOSTS} ${GEN_HOSTS}"

DELAY="2"

for HOST in $GEN_HOSTS ; do
    echo "running fpnd ${CMD_ARG} on ${HOST}"
    ssh $HOST -t sudo rc-service fpnd $CMD_ARG
    sleep $DELAY ;
    if [[ "${CMD_ARG}" = "stop" ]]; then
        ssh $HOST -t sudo rc-service -DN gkrellmd start
    fi
done

if ((failures == 0)); then
    echo "Success"
else
    echo "Failure"
    exit 1
fi

