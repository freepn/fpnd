#! /bin/sh
#
# this copies the update script to each fpnd host and then runs it
#

set -e

INFRA_HOSTS="infra-k1  infra-k2"
GEN_HOSTS="node-01 node-02 node-03 node-04"
ALL_HOSTS="${INFRA_HOSTS} ${GEN_HOSTS}"

SCRIPT="update_fpnd_local.sh"

for HOST in $GEN_HOSTS ; do
    echo "copying ${SCRIPT} to ${HOST}"
    scp $HOME/bin/$SCRIPT $HOST:~/ ;
done

for HOST in $GEN_HOSTS ; do
    echo "running ${SCRIPT} on ${HOST}"
    ssh $HOST -t bash ./$SCRIPT ;
done
