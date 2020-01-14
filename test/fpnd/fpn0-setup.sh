#!/bin/bash
#  test_stub

#set -x

failures=0
trap 'failures=$((failures+1))' ERR

DATE=$(date +%Y%m%d)
# very simple log capture
exec &> >(tee -ia /tmp/fpn0-setup-${DATE}_output.log)
exec 2> >(tee -ia /tmp/fpn0-setup-${DATE}_error.log)

#VERBOSE="anything"

ZT_UP="started"
if [[ $ZT_UP != "started" ]]; then
    echo "FPN zerotier service is not running!!"
    echo "Please start the zerotier service and re-run this script."
    exit 1
fi

[[ -n $VERBOSE ]] && echo "Checking kernel rp_filter setting..."
RP_NEED="2"
RP_ORIG="$(sysctl net.ipv4.conf.all.rp_filter | cut -f3 -d' ')"

if [[ ${RP_NEED} = "${RP_ORIG}" ]]; then
    [[ -n $VERBOSE ]] && echo "  RP good..."
else
    [[ -n $VERBOSE ]] && echo "  RP needs garlic filter..."
    # sysctl -w net.ipv4.conf.all.rp_filter=$RP_NEED > /dev/null 2>&1
fi

my_name=$(basename "$0")

if [[ ${my_name} = "fpn0-setup.sh" ]]; then
    ZT_NETWORK="bb8dead3c63cea29"
    FPN_DEV="FPN0"
else
    ZT_NETWORK="7ac4235ec5d3d938"
    FPN_DEV="FPN1"
fi

if [[ ${my_name} = *down* ]]; then
    ZT_NETWORK=""
fi

if [[ -n $ZT_NETWORK ]]; then
    [[ -n $VERBOSE ]] && echo echo "My name is: $my_name"
    [[ -n $VERBOSE ]] && echo "Using $FPN_DEV ID: $ZT_NETWORK"
else
    echo "Please provide the network ID as argument."
    exit 1
fi

IPV4_INTERFACE=$(ip -o link show up | awk -F': ' '{print $2}' | grep -e 'eth' -e 'en' -e 'wl' -e 'mlan' | head -n 1)

# set this to your "normal" network interface if needed
#IPV4_INTERFACE="eth0"
#IPV4_INTERFACE="wlan0"
[[ -n $IPV4_INTERFACE ]] || IPV4_INTERFACE="eth0"
INET_ADDRESS=$(ip address show "${IPV4_INTERFACE}" | awk '/inet / {print $2}' | cut -d/ -f1)

if [[ -n $VERBOSE ]]; then
    echo ""
    echo "Found these devices and parameters:"
    echo ""
    echo "  INET interface: ${IPV4_INTERFACE}"
    echo "  INET address: ${INET_ADDRESS}"
fi

# Populate secondary routing table
# ip route add default via ${ZT_GATEWAY} dev ${ZT_INTERFACE} table "${TABLE_NAME}"

# Anything with this fwmark will use the secondary routing table
# ip rule add fwmark 0x1 table "${TABLE_NAME}"
# sleep 2

# Mark these packets so that ip can route web traffic through fpn0
# iptables -A OUTPUT -t mangle -o ${IPV4_INTERFACE} -p tcp --dport 443 -j MARK --set-mark 1
# iptables -A OUTPUT -t mangle -o ${IPV4_INTERFACE} -p tcp --dport 80 -j MARK --set-mark 1

# now rewrite the src-addr using snat
# iptables -A POSTROUTING -t nat -s ${INET_ADDRESS} -o ${ZT_INTERFACE} -p tcp --dport 443 -j SNAT --to ${ZT_ADDRESS}
# iptables -A POSTROUTING -t nat -s ${INET_ADDRESS} -o ${ZT_INTERFACE} -p tcp --dport 80 -j SNAT --to ${ZT_ADDRESS}

[[ -n $VERBOSE ]] && echo ""
if ((failures < 1)); then
    echo "Success"
else
    echo "$failures warnings/errors"
    exit 1
fi
