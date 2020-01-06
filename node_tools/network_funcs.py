# coding: utf-8

"""Network helper functions."""
from __future__ import print_function

import logging


logger = logging.getLogger(__name__)


def get_net_cmds(home_dir):
    import os
    up0 = os.path.join(home_dir, 'fpn0-setup.sh')
    down0 = os.path.join(home_dir, 'fpn0-down.sh')
    up1 = os.path.join(home_dir, 'fpn1-setup.sh')
    down1 = os.path.join(home_dir, 'fpn1-down.sh')
    return [up0], down0, up1, down1


def run_net_cmd(cmd):
    import subprocess
    state = False
    # with shell=false cmd must be a sequence not a string
    res = subprocess.run(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         universal_newlines=True,
                         shell=False)

    if 'Success' in res.stdout:
        state = True
    return state, res
