#! /bin/sh
#
# this runs fpnd on each fpnd host with short delay in between
# use "stop" arg to overide start

CMD_ARG=${1:-start}

INFRA_HOSTS="infra-k1  infra-k2"
# node-01
GEN_HOSTS="node-01 node-02 node-03 node-04"
ALL_HOSTS="${INFRA_HOSTS} ${GEN_HOSTS}"

DELAY="2"

for HOST in $GEN_HOSTS ; do
    echo "running fpnd ${CMD_ARG} on ${HOST}"
    ssh $HOST -t sudo /etc/init.d/fpnd $CMD_ARG
    sleep $DELAY ;
    if [[ "${CMD_ARG}" = "stop" ]]; then
        ssh $HOST -t sudo /etc/init.d/gkrellmd --nodeps start
    fi
done
