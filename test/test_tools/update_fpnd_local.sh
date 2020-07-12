#!/bin/bash
#
# this rebuilds all the fpnd packages that are currently installed
#

TEMP_LIST="fpnd-pkgs.txt"
INSTALLED="fpnd-pkgs_current.txt"

USE_FLAGS="test-infra polkit"
PKGS="net-misc/fpnd app-admin/freepn-gtk3-tray"

echo "setting fpnd use flags to ${USE_FLAGS}"
sudo /bin/bash -c "echo 'net-misc/fpnd ${USE_FLAGS}' > /etc/portage/package.use/fpnd"

sudo /etc/init.d/netmount --nodeps restart

equery list $PKGS |cut -d" " -f2|grep -v ^\*$ > $TEMP_LIST

for pkg in $(cat $TEMP_LIST) ; do
    echo "rebuilding  =${pkg}"
    sudo emerge -v1 "=$pkg" ;
done

sudo sed -i -e "s|do_check=\"true\"|do_check=\"no\"|" /etc/conf.d/fpnd

equery list $PKGS |cut -d" " -f2|grep -v ^\*$ > $INSTALLED

rm $TEMP_LIST

