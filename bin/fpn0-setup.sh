#!/bin/bash
# fpn0-setup.sh v0.0
#   Configures outgoing FPN browsing interface/rules on target node
#
# PREREQS:
#   1. zt/iptables/iproute2 plus assoc. kernel modules installed on target node
#   2. network controller has available network with one "exit" node
#   3. target node has been joined and authorized on the above network
#   4. target node has ``zt`` net device with address on the above network
#   5. target node and "exit" node can ping each other on the above network
#
# NOTE you may provide the ZT network ID as the only argument if
#      it does not automatically select the correct FPN0 network ID


#set -x

failures=0
trap 'failures=$((failures+1))' ERR

DATE=$(date +%Y%m%d)
# very simple log capture
exec &> >(tee -ia /tmp/fpn0-setup-${DATE}_output.log)
exec 2> >(tee -ia /tmp/fpn0-setup-${DATE}_error.log)

#VERBOSE="anything"
#DROP_DNS_53="anything"

# set allowed ports (still TBD))
ports_to_fwd="80 443 53"

[[ -n $VERBOSE ]] && echo "Checking iptables binary..."
IPTABLES=$(find /sbin /usr/sbin -name iptables)
HAS_LEGACY=$(find /sbin /usr/sbin -name iptables-legacy)
if [[ -n $HAS_LEGACY ]]; then
    IPTABLES="${HAS_LEGACY}"
fi

[[ -n $VERBOSE ]] && echo "Checking kernel rp_filter setting..."
RP_NEED="2"
RP_ORIG="$(sysctl net.ipv4.conf.all.rp_filter | cut -f3 -d' ')"

if [[ ${RP_NEED} = "${RP_ORIG}" ]]; then
    [[ -n $VERBOSE ]] && echo "  RP good..."
else
    [[ -n $VERBOSE ]] && echo "  RP needs garlic filter..."
    sysctl -w net.ipv4.conf.all.rp_filter=$RP_NEED > /dev/null 2>&1
fi

while read -r line; do
    [[ -n $VERBOSE ]] && echo "Checking network..."
    LAST_OCTET=$(echo "$line" | cut -d" " -f9 | cut -d"/" -f1 | cut -d"." -f4)
    FULL_OCTET=$(echo "$line" | cut -d" " -f9 | cut -d"/" -f1)
    ZT_NET_ID=$(echo "$line" | cut -d" " -f3)
    ZT_IF_NAME=$(echo "$line" | cut -d" " -f8)
    ZT_NET_GW=$(zerotier-cli -j listnetworks | grep "${ZT_NET_ID}" -A 14 | grep via | awk '{ print $2 }' | tail -n 1 | cut -d'"' -f2)
    if [[ $FULL_OCTET != $ZT_NET_GW ]]; then
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

[[ -n $VERBOSE ]] && echo "Checking for FPN routing table..."
if [[ ${FPN_RT_TABLE} = "${TABLE_NAME}" ]]; then
    [[ -n $VERBOSE ]] && echo "  RT good..."
else
    [[ -n $VERBOSE ]] && echo "  Inserting routing table..."
    echo "200   ${TABLE_NAME}" >> /etc/iproute2/rt_tables
fi

if [[ -n $VERBOSE ]]; then
    echo "Checking FPN network settings..."
    zerotier-cli set "${ZT_NETWORK}" allowGlobal=1 2>&1 | grep allowGlobal
else
    zerotier-cli set "${ZT_NETWORK}" allowGlobal=1 > /dev/null 2>&1
fi

DEFAULT_IFACE=$(ip route show default | grep src | awk '{print $5}')
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
#[[ -n $IPV4_INTERFACE ]] || IPV4_INTERFACE="mlan0"
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
fi

# Populate secondary routing table
ip route add default via ${ZT_GATEWAY} dev ${ZT_INTERFACE} table "${TABLE_NAME}"

# Anything with this fwmark will use the secondary routing table
ip rule add fwmark 0x1 table "${TABLE_NAME}"
#sleep 2

# add mangle chain
$IPTABLES -N fpn0-mangleout -t mangle
$IPTABLES -t mangle -A OUTPUT -j fpn0-mangleout

# Mark these packets so that ip can route web traffic through fpn0
$IPTABLES -t mangle -A fpn0-mangleout -o ${IPV4_INTERFACE} -p tcp --dport 443 -j MARK --set-mark 1
$IPTABLES -t mangle -A fpn0-mangleout -o ${IPV4_INTERFACE} -p tcp --dport 80 -j MARK --set-mark 1
if ! [[ -n $DROP_DNS_53 ]]; then
    $IPTABLES -t mangle -A fpn0-mangleout -o ${IPV4_INTERFACE} -p udp --dport 53 -j MARK --set-mark 1
    $IPTABLES -t mangle -A fpn0-mangleout -o ${IPV4_INTERFACE} -p tcp --dport 53 -j MARK --set-mark 1
fi

# nat/postrouting chain
$IPTABLES -N fpn0-postnat -t nat
$IPTABLES -t nat -A POSTROUTING -j fpn0-postnat
# now rewrite the src-addr using snat/masq
$IPTABLES -t nat -A fpn0-postnat -s ${INET_ADDRESS} -o ${ZT_INTERFACE} -p tcp --dport 443 -j SNAT --to ${ZT_ADDRESS}
$IPTABLES -t nat -A fpn0-postnat -s ${INET_ADDRESS} -o ${ZT_INTERFACE} -p tcp --dport 80 -j SNAT --to ${ZT_ADDRESS}
if ! [[ -n $DROP_DNS_53 ]]; then
    $IPTABLES -t nat -A fpn0-postnat -s ${INET_ADDRESS} -o ${ZT_INTERFACE} -p tcp --dport 53 -j MASQUERADE
    $IPTABLES -t nat -A fpn0-postnat -s ${INET_ADDRESS} -o ${ZT_INTERFACE} -p udp --dport 53 -j MASQUERADE
fi

if [[ -n $DROP_DNS_53 ]]; then
    $IPTABLES -N fpn0-dns-dropin
    $IPTABLES -A INPUT -j fpn0-dns-dropin
    $IPTABLES -A fpn0-dns-dropin -i lo -j ACCEPT
    $IPTABLES -A fpn0-dns-dropin ! -i lo -s 127.0.0.0/8 -j REJECT
    $IPTABLES -N fpn0-dns-dropout
    $IPTABLES -A OUTPUT -j fpn0-dns-dropout
    $IPTABLES -A fpn0-dns-dropout -o lo -j ACCEPT

    $IPTABLES -A fpn0-dns-dropout -t filter -p udp --dport 53 -m limit --limit 5/min -j LOG --log-prefix "DROP PORT 53: " --log-level 7
    $IPTABLES -A fpn0-dns-dropout -t filter -p udp --dport 53 -j DROP
    $IPTABLES -A fpn0-dns-dropout -t filter -p tcp --dport 53 -m limit --limit 5/min -j LOG --log-prefix "DROP PORT 53: " --log-level 7
    $IPTABLES -A fpn0-dns-dropout -t filter -p tcp --dport 53 -j DROP
fi

[[ -n $VERBOSE ]] && echo ""
if ((failures < 1)); then
    echo "Success"
else
    echo "$failures warnings/errors"
    exit 1
fi
