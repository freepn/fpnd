#! /usr/bin/env bash
# show-geoip.sh
#

set -e

PATH=/usr/bin:/bin:/usr/sbin:/sbin
export LC_ALL=C

# environemt vars
# use doh for curl if we have a server FQDN
#DOH_HOST=${1:-}
#VERBOSE="anything"

TEMP_DIR="/tmp"
RUN_DIR="/run/fpnd"
[[ -d "${RUN_DIR}" ]] && TEMP_DIR="${RUN_DIR}"

# Fetch data from Ubuntu's geoip server, requires route to internet
xml_file="${TEMP_DIR}/geoip-location.xml"
log_file="${TEMP_DIR}/wget.log"
clog_file="${TEMP_DIR}/curl.log"
wget_args="--timeout=1 --waitretry=0 --tries=5"

TMP_FILES="${xml_file} ${log_file} ${clog_file}"
for tempfile in "${TMP_FILES}"; do
    [[ -f $tempfile ]] && rm -f $tempfile
done

# use --doh-url if curl is new enough
CURL_SEMVER=$(curl --version | head -n1 | awk '{ print $2 }')
CURL_BASEVER="7.62.0"
doh_arg=""

# FUNC semver_to_int
# converts a "semantic version" string to integer for sorting and comparison
# version components can range from 0 - 999
semver_to_int() {
    local IFS=.
    parts=($1)
    (( val=1000000*parts[0]+1000*parts[1]+parts[2] ))
    echo $val
}

CURL_INT=$(semver_to_int "${CURL_SEMVER}")
CURL_BASE=$(semver_to_int "${CURL_BASEVER}")

#if [[ $CURL_INT -ge $CURL_BASE ]]; then
    #if [[ -n $DOH_HOST ]]; then
        #doh_arg="--doh-url https://${DOH_HOST}/dns-query"
        #if [[ -n $VERBOSE ]]; then
            #echo "Using curl doh_arg valus: $doh_arg"
        #fi
    #fi
    #/usr/bin/curl --stderr $clog_file --silent -m 3 $doh_arg https://geoip.ubuntu.com/lookup > $xml_file
#fi

/usr/bin/wget $wget_args -o $log_file -O - -q https://geoip.ubuntu.com/lookup > $xml_file

if ! [[ -s $xml_file ]]; then
    /usr/bin/wget $wget_args --retry-connrefused -o $log_file -O - -q https://geoip.ubuntu.com/lookup > $xml_file
fi

IP_ADDR=$(cat $xml_file | sed -n -e 's/.*<Ip>\(.*\)<\/Ip>.*/\1/p')
LAT_FULL=$(cat $xml_file | sed -n -e 's/.*<Latitude>\(.*\)<\/Latitude>.*/\1/p')
LON_FULL=$(cat $xml_file | sed -n -e 's/.*<Longitude>\(.*\)<\/Longitude>.*/\1/p' | cut -d"-" -f2)
CITY=$(cat $xml_file | sed -n -e 's/.*<City>\(.*\)<\/City>.*/\1/p')
STATE=$(cat $xml_file | sed -n -e 's/.*<RegionCode>\(.*\)<\/RegionCode>.*/\1/p')
COUNTRY=$(cat $xml_file | sed -n -e 's/.*<CountryCode>\(.*\)<\/CountryCode>.*/\1/p')
ZIPCODE=$(cat $xml_file | sed -n -e 's/.*<ZipPostalCode>\(.*\)<\/ZipPostalCode>.*/\1/p')

LAT=$(printf "%.2f" "$LAT_FULL")
LON=$(printf "%.2f" "$LON_FULL")
LOCATION="$CITY, $STATE $ZIPCODE ($COUNTRY)"

if [[ "${CITY}" = "None" ]]; then
    echo "Public IP and geolocation: ${IP_ADDR}, ${LAT} ${LON} ($COUNTRY)"
else
    echo "Public IP and geolocation: ${IP_ADDR}, ${LOCATION}"
fi
