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
#DROP_DNS_53="anything"

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
    echo "Please provide the network ID as argument."
    exit 1
fi

ZT_INTERFACE=$(zerotier-cli get "${ZT_NETWORK}" portDeviceName)
ZT_ADDRESS=$(zerotier-cli get "${ZT_NETWORK}" ip4)
ZT_GATEWAY=$(zerotier-cli -j listnetworks | grep "${ZT_INTERFACE}" -A 14 | grep via | awk '{ print $2 }' | tail -n 1 | cut -d'"' -f2)

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

DEFAULT_IFACE=$(ip route show default | awk '{print $5}')
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

# set this to your "normal" network interface if needed
#IPV4_INTERFACE="eth0"
#IPV4_INTERFACE="wlan0"
[[ -n $IPV4_INTERFACE ]] || IPV4_INTERFACE="mlan0"
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
if [[ -n $DROP_DNS_53 ]]; then
    $IPTABLES -D OUTPUT -t filter -p tcp --dport 53 -j DROP
    $IPTABLES -D OUTPUT -t filter -p tcp --dport 53 -m limit --limit 5/min -j LOG --log-prefix "DROP PORT 53: " --log-level 7
    $IPTABLES -D OUTPUT -t filter -p udp --dport 53 -j DROP
    $IPTABLES -D OUTPUT -t filter -p udp --dport 53 -m limit --limit 5/min -j LOG --log-prefix "DROP PORT 53: " --log-level 7
    $IPTABLES -D OUTPUT -o lo -j ACCEPT
    $IPTABLES -D INPUT ! -i lo -s 127.0.0.0/8 -j REJECT
    $IPTABLES -D INPUT -i lo -j ACCEPT
fi

if ! [[ -n $DROP_DNS_53 ]]; then
    $IPTABLES -D POSTROUTING -t nat -s ${INET_ADDRESS} -o ${ZT_INTERFACE} -p tcp --dport 53 -j SNAT --to ${ZT_ADDRESS}
    $IPTABLES -D POSTROUTING -t nat -s ${INET_ADDRESS} -o ${ZT_INTERFACE} -p udp --dport 53 -j SNAT --to ${ZT_ADDRESS}
fi
$IPTABLES -D POSTROUTING -t nat -s ${INET_ADDRESS} -o ${ZT_INTERFACE} -p tcp --dport 443 -j SNAT --to ${ZT_ADDRESS}
$IPTABLES -D POSTROUTING -t nat -s ${INET_ADDRESS} -o ${ZT_INTERFACE} -p tcp --dport 80 -j SNAT --to ${ZT_ADDRESS}

if ! [[ -n $DROP_DNS_53 ]]; then
    $IPTABLES -D OUTPUT -t mangle -o ${IPV4_INTERFACE} -p tcp --dport 53 -j MARK --set-mark 1
    $IPTABLES -D OUTPUT -t mangle -o ${IPV4_INTERFACE} -p udp --dport 53 -j MARK --set-mark 1
fi
$IPTABLES -D OUTPUT -t mangle -o ${IPV4_INTERFACE} -p tcp --dport 443 -j MARK --set-mark 1
$IPTABLES -D OUTPUT -t mangle -o ${IPV4_INTERFACE} -p tcp --dport 80 -j MARK --set-mark 1

[[ -n $VERBOSE ]] && echo ""
if ((failures < 1)); then
    echo "Success"
else
    echo "$failures warnings/errors"
    exit 1
fi
