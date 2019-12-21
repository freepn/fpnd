#!/bin/bash
# fpn1-setup.sh v0.0
#   Configures incoming FPN routing interface/rules on target node
#
# PREREQS:
#   1. zt/iptables/iproute2 plus assoc. kernel modules installed on target node
#   2. network controller has available network with global default route
#   3. target node has been joined and authorized on the above network
#   4. target node has been configured as default gateway on the above network
#
# NOTE you may provide the ZT network ID as the only argument if
#      it does not automatically select the correct FPN1 network ID

#set -x

failures=0
trap 'failures=$((failures+1))' ERR

DATE=$(date +%Y%m%d)
# very simple log capture
exec &> >(tee -ia /tmp/fpn1-setup-${DATE}_output.log)
exec 2> >(tee -ia /tmp/fpn1-setup-${DATE}_error.log)

# uncomment for more output
#VERBOSE="anything"

# uncomment AND set if you have a weird interface name that depends
# on eth0 UP but null, eg, this is needed on espressobin
#ETH0_NULL="lan1"

ZT_UP=$(/etc/init.d/zerotier status | grep -o started)
if [[ $ZT_UP != "started" ]]; then
    [[ -n $VERBOSE ]] && echo "FPN zerotier service is not running!!"
    [[ -n $VERBOSE ]] && echo "Please start the zerotier service and then re-run this script."
    exit 1
fi

zt_route_tgts=( $(ip route show | grep zt | cut -d" " -f3) )
num_zt_tgts=${#zt_route_tgts[@]}

if ((num_zt_tgts < 1)); then
    echo "No FPN networks found!!"
    echo "Has this device joined a network yet?"
    exit 1
elif ((num_zt_tgts < 2)); then
    echo "Only 1 FPN network found!!"
    echo "Has this device joined a second network yet?"
    exit 1
elif ((num_zt_tgts = 2)); then
    [[ -n $VERBOSE ]] && echo "Two FPN networks found, parsing network IDs..."
fi

while read -r line; do
    [[ -n $VERBOSE ]] && echo "Checking network..."
    LAST_OCTET=$(echo "$line" | cut -d"/" -f2 | cut -d"," -f2 | cut -d'.' -f4)
    ZT_NET_ID=$(echo "$line" | cut -d" " -f3)
    if [[ $LAST_OCTET = 1 ]]; then
        ZT_SRC_NETID="${ZT_NET_ID}"
        [[ -n $VERBOSE ]] && echo "  Found $ZT_SRC_NETID"
        break
    else
        [[ -n $VERBOSE ]] && echo "  No gateway found"
    fi
done < <(zerotier-cli listnetworks | grep zt)

ZT_SRC_NETID=${1:-$ZT_SRC_NETID}

if [[ -n $ZT_SRC_NETID ]]; then
    [[ -n $VERBOSE ]] && echo "Using FPN1 ID: $ZT_SRC_NETID"
else
    echo "Please provide the network ID as argument."
    exit 1
fi

ZT_INTERFACE=$(zerotier-cli get "${ZT_SRC_NETID}" portDeviceName)
ZT_SRC_ADDR=$(zerotier-cli get "${ZT_SRC_NETID}" ip4)

# this should be the active interface with default route
IPV4_INTERFACE=$(ip -o link show up | awk -F': ' '{print $2}' | grep -e 'en' -e 'wl' -e 'lan' -e 'wan' -e 'eth' | head -n 1)
INET_GATEWAY=$(ip route show | awk '/default / {print $3}')

if [[ -n $ETH0_NULL ]]; then
    IPV4_INTERFACE="${ETH0_NULL}"
fi

INET_ADDRESS=$(ip address show "${IPV4_INTERFACE}" | awk '/inet / {print $2}' | cut -d/ -f1)
ZT_SRC_NET=$(ip route show | grep ${ZT_INTERFACE} | awk '{print $1}')

if [[ -n $VERBOSE ]]; then
    echo "Found these devices and parameters:"
    echo "  FPN SRC interface: ${ZT_INTERFACE}"
    echo "  FPN SRC address: ${ZT_SRC_ADDR}"
    echo "  FPN SRC network: ${ZT_SRC_NET}"
    echo "  FPN SRC network id: ${ZT_SRC_NETID}"
    echo ""
    echo "  INET interface: ${IPV4_INTERFACE}"
    echo "  INET address: ${INET_ADDRESS}"
    echo "  INET gateway: ${INET_GATEWAY}"
fi

if [[ -n $VERBOSE ]]; then
    echo "Allow forwarding for FPN source traffic"
    sysctl -w net.ipv4.ip_forward=1
else
    sysctl -w net.ipv4.ip_forward=1 > /dev/null 2>&1
fi

# setup nat/masq to forward outbound/return traffic
iptables -t nat -A POSTROUTING -o "${IPV4_INTERFACE}" -s "${ZT_SRC_NET}" -j SNAT --to-source "${INET_ADDRESS}"
iptables -A FORWARD -i "${ZT_INTERFACE}" -o "${IPV4_INTERFACE}" -s "${ZT_SRC_NET}" -p tcp --dport 80 -j ACCEPT
iptables -A FORWARD -i "${ZT_INTERFACE}" -o "${IPV4_INTERFACE}" -s "${ZT_SRC_NET}" -p tcp --dport 443 -j ACCEPT
iptables -A FORWARD -i "${IPV4_INTERFACE}" -o "${ZT_INTERFACE}" -d "${ZT_SRC_NET}" -p tcp --sport 80 -j ACCEPT
iptables -A FORWARD -i "${IPV4_INTERFACE}" -o "${ZT_INTERFACE}" -d "${ZT_SRC_NET}" -p tcp --sport 443 -j ACCEPT

[[ -n $VERBOSE ]] && echo ""
if ((failures < 1)); then
    echo "Success"
else
    echo "$failures warnings/errors"
    exit 1
fi
