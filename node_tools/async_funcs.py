# coding: utf-8

"""asyncio-specific wrapper functions."""

import asyncio
import aiohttp
import logging


logger = logging.getLogger(__name__)


async def add_network_object(client, net_id=None, mbr_id=None, ctlr_id=None):
    """
    Command wrapper for creating ZT objects under the ``controller`` endpoint.
    Required arguments are ``client`` and either one of the following:
        ``net_id`` *and* ``mbr_id`` to create a member object *or* just
        ``ctlr_id`` to create a network object.
    :param client: ztcli_api client object
    :param net_id: network ID endpoint path
    :param mbr_id: member ID endpoint path
    :param ctlr_id: network controller ID
    """
    from node_tools.ctlr_funcs import name_generator

    if net_id and mbr_id:
        endpoint = 'controller/network/{}/member/{}'.format(net_id, mbr_id)
        cfg_dict = {'': ''}
    elif ctlr_id:
        net_name = name_generator()
        endpoint = 'controller/network/{}'.format(ctlr_id + '______')
        cfg_dict = {'name': net_name}
    else:
        logger.error('One or more required arguments not found!')
        return

    await client.set_value(cfg_dict, endpoint)


async def delete_network_object(client, net_id, mbr_id=None):
    """
    Command wrapper for deleting ZT objects under the ``controller`` endpoint.
    Required arguments are ``client`` and either one of the following:
        ``net_id`` *and* ``mbr_id`` to delete a member object *or* just
        ``net_id`` to delete a network object.
    Warning: deleting a network object is permanent.
    :param client: ztcli_api client object
    :param net_id: network ID endpoint path
    :param mbr_id: member ID endpoint path
    """
    if mbr_id and net_id:
        endpoint = 'controller/network/{}/member/{}'.format(net_id, mbr_id)
    elif net_id:
        endpoint = 'controller/network/{}'.format(net_id)
    else:
        logger.error('One or more required arguments not found!')
        return

    await client.delete_thing(endpoint)


async def get_network_object_data(client, net_id, mbr_id=None):
    """
    Command wrapper for getting ZT network/member data under the
    ``controller`` endpoint.
    Required arguments are ``client`` and either one of the following:
        ``net_id`` *and* ``mbr_id`` to get member data *or* just
        ``net_id`` to get network data.
    :param client: ztcli_api client object
    :param net_id: network ID endpoint path
    :param mbr_id: member ID endpoint path
    """
    if mbr_id and net_id:
        endpoint = 'controller/network/{}/member/{}'.format(net_id, mbr_id)
    elif net_id:
        endpoint = 'controller/network/{}'.format(net_id)
    else:
        logger.error('One or more required arguments not found!')
        return

    await client.get_data(endpoint)


async def get_network_object_ids(client, net_id=None):
    """
    Command wrapper for getting ZT network/member objects under the
    ``controller`` endpoint.
    Required arguments are ``client`` and optionally ``net_id`` to get
    member IDs from a network.
    :param client: ztcli_api client object
    :param net_id: network ID endpoint path
    """
    if net_id:
        endpoint = 'controller/network/{}/member'.format(net_id)
    else:
        endpoint = 'controller/network'

    await client.get_data(endpoint)
