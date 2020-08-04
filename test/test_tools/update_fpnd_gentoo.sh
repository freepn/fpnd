#!/bin/bash
#
# this rebuilds all (gentoo) fpnd packages that are currently installed
#

failures=0
trap 'failures=$((failures+1))' ERR

TEMP_LIST="fpnd-pkgs.txt"
INSTALLED="fpnd-pkgs_current.txt"

USE_FLAGS="test-infra polkit"
PKGS="net-misc/fpnd app-admin/freepn-gtk3-tray"

echo "setting fpnd use flags to ${USE_FLAGS}"
sudo /bin/bash -c "echo 'net-misc/fpnd ${USE_FLAGS}' > /etc/portage/package.use/fpnd"

sudo rc-service -Di netmount restart

equery list $PKGS |cut -d" " -f2|grep -v ^\*$ > $TEMP_LIST

for pkg in $(cat $TEMP_LIST) ; do
    echo "rebuilding  =${pkg}"
    sudo emerge -q "=$pkg" ;
done

sudo sed -i -e "s|do_check=\"true\"|do_check=\"no\"|" /etc/conf.d/fpnd

equery list $PKGS |cut -d" " -f2|grep -v ^\*$ > $INSTALLED

rm $TEMP_LIST

if ((failures == 0)); then
    echo "Success"
else
    echo "Failure"
    exit 1
fi

