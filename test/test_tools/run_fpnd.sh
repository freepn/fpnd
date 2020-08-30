#! /bin/sh
#
# this runs fpnd on each gentoo host with short delay in between
# use "stop" or "status" arg to overide start

failures=0
trap 'failures=$((failures+1))' ERR

CMD_ARG=${1:-start}

INFRA_HOSTS="infra-01 infra-02 exit-01"
# node-05 node-01
GEN_HOSTS="node-02 node-03 node-04"
CHK_HOSTS="node-01 node-02 node-03 node-04 node-05"
ALL_HOSTS="${INFRA_HOSTS} ${CHK_HOSTS}"

DELAY="2"

if [[ "${CMD_ARG}" = "status" ]]; then
    for HOST in $CHK_HOSTS ; do
        NODE_STATE=$(ssh -q "${HOST}" -t tail -n 1 /run/fpnd/fpnd.state)
        echo "${HOST} state is ${NODE_STATE}"
    done
else
    for HOST in $GEN_HOSTS ; do
        NODE_ID=$(ssh "${HOST}" -t sudo zerotier-cli info | awk '{print $3}' | tail -n1)
        echo "running fpnd ${CMD_ARG} on ${HOST} with id ${NODE_ID}"
        #ssh $HOST -t sudo rc-service mini-dot stop
        ssh $HOST -t sudo rc-service fpnd $CMD_ARG
        sleep $DELAY ;
        if [[ "${CMD_ARG}" = "stop" ]]; then
            ssh $HOST -t sudo rc-service stunnel.fpnd $CMD_ARG
            ssh $HOST -t sudo rc-service -DN gkrellmd start
        fi
    done
fi

if ((failures == 0)); then
    echo "Success"
else
    echo "Failure"
    exit 1
fi
