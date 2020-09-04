#!/bin/bash
# fpn0-down.sh v0.0
#   Deconfigures outgoing FPN browsing interface/rules on target node
#
# PREREQS:
#   1. The fpn0-setup.sh script has been run
#   2. current test is complete
#

#set -x

failures=0
trap 'failures=$((failures+1))' ERR

DATE=$(date +%Y%m%d)
# very simple log capture
exec &> >(tee -ia /tmp/fpn0-down-${DATE}_output.log)
exec 2> >(tee -ia /tmp/fpn0-down-${DATE}_error.log)

#VERBOSE="anything"
#DROP_DNS_53="anything"  <= fpnd.ini
# set the preferred network interface if needed
#SET_IPV4_IFACE="eth0"  <= fpnd.ini

# set allowed ports (still TBD))
ports_to_fwd="http https domain submission imaps ircs ircs-u"

[[ -n $VERBOSE ]] && echo "Checking iptables binary..."
IPTABLES=$(find /sbin /usr/sbin -name iptables)
HAS_LEGACY=$(find /sbin /usr/sbin -name iptables-legacy)
if [[ -n $HAS_LEGACY ]]; then
    IPTABLES="${HAS_LEGACY}"
fi

[[ -n $VERBOSE ]] && echo "Checking kernel rp_filter setting..."
RP_NEED="1"
RP_ORIG="$(sysctl net.ipv4.conf.all.rp_filter | cut -f3 -d' ')"

if [[ ${RP_NEED} = "${RP_ORIG}" ]]; then
    [[ -n $VERBOSE ]] && echo "  RP good..."
else
    [[ -n $VERBOSE ]] && echo "  RP remove garlic filter..."
    sysctl -w net.ipv4.conf.all.rp_filter=$RP_NEED > /dev/null 2>&1
fi

while read -r line; do
    [[ -n $VERBOSE ]] && echo "Checking network..."
    LAST_OCTET=$(echo "$line" | cut -d" " -f9 | cut -d"/" -f1 | cut -d"." -f4)
    FULL_OCTET=$(echo "$line" | cut -d" " -f9 | cut -d"/" -f1)
    ZT_NET_ID=$(echo "$line" | cut -d" " -f3)
    ZT_IF_NAME=$(echo "$line" | cut -d" " -f8)
    ZT_NET_GW=$(zerotier-cli -j listnetworks | grep "${ZT_NET_ID}" -A 14 | grep via | awk '{ print $2 }' | tail -n 1 | cut -d'"' -f2)
    if [[ $LAST_OCTET != 1 && $FULL_OCTET != $ZT_NET_GW ]]; then
        ZT_NETWORK="${ZT_NET_ID}"
        [[ -n $VERBOSE ]] && echo "  Found $ZT_NETWORK"
        break
    else
        [[ -n $VERBOSE ]] && echo "  Skipping gateway network"
    fi
done < <(zerotier-cli listnetworks | grep zt)

ZT_NETWORK=${1:-$ZT_NETWORK}

if [[ -n $ZT_NETWORK ]]; then
    [[ -n $VERBOSE ]] && echo "Using FPN0 ID: $ZT_NETWORK"
else
    [[ -n $VERBOSE ]] && echo "No network ID found, continuing anyway..."
fi

if [[ -n $ZT_NETWORK ]]; then
    ZT_INTERFACE=$(zerotier-cli get "${ZT_NETWORK}" portDeviceName)
    ZT_ADDRESS=$(zerotier-cli get "${ZT_NETWORK}" ip4)
    ZT_GATEWAY=$(zerotier-cli -j listnetworks | grep "${ZT_INTERFACE}" -A 14 | grep via | awk '{ print $2 }' | tail -n 1 | cut -d'"' -f2)
fi

TABLE_NAME="fpn0-route"
TABLE_PATH="/etc/iproute2/rt_tables"
FPN_RT_TABLE=$(cat "${TABLE_PATH}" | { grep -o "${TABLE_NAME}" || test $? = 1; })
FPN_RT_PRIO=$(ip rule show | grep "${TABLE_NAME}" | cut -d':' -f1)

[[ -n $VERBOSE ]] && echo "Checking for FPN routing table..."
if [[ ${FPN_RT_TABLE} = "${TABLE_NAME}" ]]; then
    [[ -n $VERBOSE ]] && echo "  Flushing route cache..."
    ip route flush cache
    while read -r line; do
        [[ -n $VERBOSE ]] && echo "  Removing route rule..."
        ip rule del prio "${line}"
    done < <(ip rule show | grep "${TABLE_NAME}" | cut -d':' -f1)
    [[ -n $VERBOSE ]] && echo "  Deleting route..."
    ip route del default via ${ZT_GATEWAY} dev ${ZT_INTERFACE} table "${TABLE_NAME}"
    [[ -n $VERBOSE ]] && echo "  Cleaning up..."
    sed -i "/${FPN_RT_TABLE}/d" /etc/iproute2/rt_tables
else
    [[ -n $VERBOSE ]] && echo "  FPN routing table not found!!"
fi

if [[ -n $SET_IPV4_IFACE ]]; then
    [[ -n $VERBOSE ]] && echo "Looking for $SET_IPV4_IFACE"
    TEST_IFACE=$(ip route show default | { grep -o "${SET_IPV4_IFACE}" || test $? = 1; })
    if [[ -n $TEST_IFACE ]]; then
        [[ -n $VERBOSE ]] && echo "  $TEST_IFACE looks good..."
        IPV4_INTERFACE="${TEST_IFACE}"
    else
        [[ -n $VERBOSE ]] && echo "  $TEST_IFACE not found!"
        DEFAULT_IFACE=$(ip route show default | awk '{print $5}' | head -n 1)
    fi
else
    DEFAULT_IFACE=$(ip route show default | awk '{print $5}' | head -n 1)
fi

if ! [[ -n $IPV4_INTERFACE ]]; then
    while read -r line; do
        [[ -n $VERBOSE ]] && echo "Checking interfaces..."
        IFACE=$(echo "$line")
        if [[ $DEFAULT_IFACE = $IFACE ]]; then
            IPV4_INTERFACE="${IFACE}"
            [[ -n $VERBOSE ]] && echo "  Found interface $IFACE"
            break
        else
            [[ -n $VERBOSE ]] && echo "  Skipping $IFACE"
        fi
    done < <(ip -o link show up  | awk -F': ' '{print $2}' | grep -v lo)
fi

if ! [[ -n $IPV4_INTERFACE ]]; then
    echo "No usable network interface found! (check settings?)"
    exit 1
fi

INET_ADDRESS=$(ip address show "${IPV4_INTERFACE}" | awk '/inet / {print $2}' | cut -d/ -f1)

if [[ -n $VERBOSE ]]; then
    echo ""
    echo "Found these devices and parameters:"
    echo "  FPN interface: ${ZT_INTERFACE}"
    echo "  FPN address: ${ZT_ADDRESS}"
    echo "  FPN gateway: ${ZT_GATEWAY}"
    echo "  FPN network id: ${ZT_NETWORK}"
    echo ""
    echo "  INET interface: ${IPV4_INTERFACE}"
    echo "  INET address: ${INET_ADDRESS}"
    echo ""
fi

[[ -n $VERBOSE ]] && echo "Deleting nat and mangle rules..."
# get fpn1 iptables state, remove custom chain rules, restore state
"$IPTABLES"-save > /tmp/fpn0-up-state.txt
sed -i '/fpn0-mangleout/d' /tmp/fpn0-up-state.txt
sed -i '/fpn0-postnat/d' /tmp/fpn0-up-state.txt
if [[ -n $DROP_DNS_53 ]]; then
    sed -i '/fpn0-dns-dropin/d' /tmp/fpn0-up-state.txt
    sed -i '/fpn0-dns-dropout/d' /tmp/fpn0-up-state.txt
fi
"$IPTABLES"-restore < /tmp/fpn0-up-state.txt
rm -f /tmp/fpn0-up-state.txt

[[ -n $VERBOSE ]] && echo ""
if ((failures < 1)); then
    echo "Success"
else
    echo "$failures warnings/errors"
    exit 1
fi
