#! /bin/sh
#
# this copies the gentoo update script to each fpnd host and then runs it
#

failures=0
trap 'failures=$((failures+1))' ERR

set -e

# override DO_ALL on the commnd line to also update infra nodes
#DO_ALL="anything"

INFRA_HOSTS="infra-01 infra-02 exit-01"
# node-04
GEN_HOSTS="node-01 node-02 node-03 node-04 node-05"
#GEN_HOSTS="node-02 node-03 node-04"
ALL_HOSTS="${INFRA_HOSTS} ${GEN_HOSTS}"

[[ -n $DO_ALL ]] && GEN_HOSTS="${ALL_HOSTS}"

SCRIPT="update_fpnd_gentoo.sh"

for HOST in $GEN_HOSTS ; do
    echo "copying ${SCRIPT} to ${HOST}"
    scp $HOME/bin/$SCRIPT $HOST:~/ ;
done

for HOST in $GEN_HOSTS ; do
    echo "running ${SCRIPT} on ${HOST}"
    ssh $HOST -t bash ./$SCRIPT $HOST ;
done

if ((failures == 0)); then
    echo "Success"
else
    echo "Failure"
    exit 1
fi

