#!/bin/bash
#
# this rebuilds all (gentoo) fpnd packages that are currently installed
#

failures=0
trap 'failures=$((failures+1))' ERR

TEMP_LIST="fpnd-pkgs.txt"
INSTALLED="fpnd-pkgs_current.txt"

USE_FLAGS="test-infra polkit"
PKGS="net-misc/fpnd-9999"
#PKGS="net-misc/stunnel-5.56-r1 net-misc/fpnd-9999 app-admin/freepn-gtk3-tray-9999"
CHK_DM=$(qlist -ICv gdm sddm lightdm slim)
if [[ -n $CHK_DM ]]; then
    PKGS="${PKGS} app-admin/freepn-gtk3-tray-9999"
fi

UNAME_N=$(uname -n)

sudo rc-service -N zerotier start
NODE_ID=$(sudo zerotier-cli info | awk '{print $3}')

#find /etc/ -name ._cfg\*stunnel -o -name ._cfg\*fpnd | sudo xargs rm -f

echo "setting fpnd use flags to ${USE_FLAGS} on ${UNAME_N}"
sudo /bin/bash -c "echo 'net-misc/fpnd ${USE_FLAGS}' > /etc/portage/package.use/fpnd"

CHK_SVC=$(sudo rc-service -N nfsclient start)
if [[ -n $CHK_SVC ]]; then
    sudo rc-service netmount restart
else
    sudo rc-service -N netmount start
fi

equery list -o $PKGS | cut -d" " -f2|grep -v ^\*$ > $TEMP_LIST

for pkg in $(cat $TEMP_LIST) ; do
    echo "rebuilding  =${pkg} for ${NODE_ID}"
    sudo emerge -q "=$pkg" ;
done

#sudo chown stunnel: /var/log/stunnel-fpnd.log
#sudo rc-service -N stunnel.fpnd restart

sudo sed -i -e "s|do_check=\"true\"|do_check=\"no\"|" /etc/conf.d/fpnd

equery list $PKGS |cut -d" " -f2|grep -v ^\*$ > $INSTALLED

rm $TEMP_LIST

if ((failures == 0)); then
    echo "Success"
else
    echo "Failure"
    exit 1
fi
