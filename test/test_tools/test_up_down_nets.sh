#!/bin/sh
# run join/leave commands to generate log data

# sudo zerotier-cli leave b6079f73c63cea29

cmds="join leave"

nets="b6079f73c63cea29 8bd5124fd6e3d938"


run_one_cmd() {
	sudo zerotier-cli $1 b6079f73c63cea29
}

run_two_cmd() {
	sudo zerotier-cli $1 b6079f73c63cea29
	sleep 1
	sudo zerotier-cli $1 8bd5124fd6e3d938
}

RANGE=3

for (( ; ; ))
do

number=$RANDOM
let "number %= $RANGE"

if [[ $number > 0 ]]; then
	if [[ $number < 2 ]]; then
		run_one_cmd join
		sleep 9
		run_one_cmd leave
	else
		run_two_cmd join
		sleep 9
		run_two_cmd leave
	fi
	sleep 5
fi

done
