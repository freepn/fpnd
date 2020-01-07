# coding: utf-8

"""Network helper functions."""
from __future__ import print_function

import logging

from node_tools.helper_funcs import NODE_SETTINGS


logger = logging.getLogger(__name__)


def get_net_cmds(bin_dir, iface=None, state=False):
    import os

    if not os.path.isdir(bin_dir):
        res = None

    if iface:
        cmds = ['fpn0-setup.sh', 'fpn0-down.sh', 'fpn1-setup.sh', 'fpn1-down.sh']
        cmd_str = 'down'
        if state:
            cmd_str = 'setup'
        for cmd in cmds:
            if iface in cmd and cmd_str in cmd:
                res = os.path.join(bin_dir, cmd)
        if not os.path.isfile(res):
            res = None
    else:
        up0 = os.path.join(bin_dir, 'fpn0-setup.sh')
        down0 = os.path.join(bin_dir, 'fpn0-down.sh')
        up1 = os.path.join(bin_dir, 'fpn1-setup.sh')
        down1 = os.path.join(bin_dir, 'fpn1-down.sh')
        res = [up0], [down0], [up1], [down1]

        if not os.path.isfile(res[0][0]):
            res = None

    return res


def run_net_cmd(cmd):
    import os
    import subprocess

    res = b''
    state = False
    head, tail = os.path.split(cmd[0])
    if not tail:
        logger.error('Bad cmd or path: {}'.format(cmd[0]))

    # with shell=false cmd must be a sequence not a string
    try:
        b = subprocess.Popen(cmd,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             shell=False)

        out, err = b.communicate()
        retcode = b.returncode

        if err:
            logger.error('net cmd {} err: {}'.format(tail, err.decode().strip()))
            res = err
        elif 'Success' in out.decode().strip():
            state = True
            res = out
            logger.debug('net cmd {} result: {}'.format(tail, out.decode().strip()))

    except Exception as exc:
        logger.error('net cmd {} exception: {}'.format(tail, exc))
        retcode = exc

    return state, res, retcode
