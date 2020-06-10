#! /usr/bin/env bash
# check-geoip.sh
#

set -e

PATH=/usr/bin:/bin:/usr/sbin:/sbin
export LC_ALL=C

# Fetch data from Ubuntu's geoip server, requires route to internet
xml_file="/tmp/geoip-location.xml"
log_file="/tmp/wget.log"

/usr/bin/wget -T 3 -t 1 -o $log_file -O - -q https://geoip.ubuntu.com/lookup > $xml_file

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

echo "Public IP and geolocation: ${IP_ADDR}, ${LOCATION}"
