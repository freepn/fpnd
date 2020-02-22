# coding: utf-8

"""ctlr-specific helper functions."""
import logging

from node_tools.cache_funcs import find_keys
from node_tools.cache_funcs import get_node_status
from node_tools.cache_funcs import load_cache_by_type


logger = logging.getLogger(__name__)


def name_generator(size=10, char_set=None):
    """
    Generate a random network name for ZT create_network_object. The
    name returned is two substrings of <size> concatenated together
    with an underscore. Default character set is lowercase ascii plus
    digits, default size is 10.
    :param size: size of each substring
    :param char_set: character set used for sub strings
    """
    import random

    if not char_set:
        import string
        chars = string.ascii_lowercase + string.digits
    else:
        chars = char_set

    str1 = ''.join(random.choice(chars) for _ in range(size))
    str2 = ''.join(random.choice(chars) for _ in range(size))
    return str1 + '_' + str2


async def create_network_object(client, net_id=None, mbr_id=None, ctlr_id=None):
    """
    Command wrapper for creating ZT objects under the ``controller`` endpoint.
    Required arguments are either one of the following:
        ``net_id`` *and* ``mbr_id`` for creating a new member object *or*
        ``ctlr_id`` for creating a new network object
    :param client: ztcli_api client object
    :param net_id: network ID endpoint path
    :param mbr_id: member ID endpoint path
    :param ctlr_id: network controller ID
    """
    if net_id and mbr_id:
        endpoint = 'controller/network/{}/member/{}'.format(net_id, mbr_id)
        args = endpoint
    elif ctlr_id:
        net_name = name_generator()
        endpoint = 'controller/network/{}'.format(ctlr_id + '______')
        args = 'name', net_name, endpoint
    else:
        logger.error('One or more required arguments not found!')
        return None

    await client.set_value(args)
    return client


async def delete_network_object(client, net_id, mbr_id=None):
    """
    Command wrapper for deleting ZT objects under the ``controller`` endpoint.
    Required arguments are either one of the following:
        ``net_id`` *and* ``mbr_id`` for deleting a member object *or*
        ``net_id`` for deleting a network object
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
        return None

    await client.delete_thing(endpoint)
    return client


def check_net_trie(trie):
    """
    Check shared state Trie is fresh and empty (mainly on startup)
    :param trie: newly instantiated ``datrie.Trie(alpha_set)``
    """
    try:
        assert trie.is_dirty()
        assert list(trie) == []
    except:
        return False
    return True


def create_state_trie(prefix='trie', ext='.dat'):
    import string
    import tempfile
    import datrie

    fd, fname = tempfile.mkstemp(suffix=ext, prefix=prefix)
    trie = datrie.Trie(string.hexdigits)
    trie.save(fname)

    return fd, fname


def load_state_trie(fname):
    import datrie

    trie = datrie.Trie.load(fname)
    return trie


def save_state_trie(trie, fname):
    trie.save(fname)


def gen_netobj_queue(deque, ipnet='172.16.0.0/12'):
    import ipaddress

    if len(deque) > 0:
        logger.debug('Using existing queue: {}'.format(deque.directory))
    else:
        logger.debug('Generating netobj queue, please be patient...')
        netobjs = list(ipaddress.ip_network(ipnet).subnets(new_prefix=30))
        for net in netobjs:
            deque.append(net)
    logger.debug('{} IPv4 network objects in queue: {}'.format(len(deque), deque.directory))


def process_netobj(netobj):
    """
    Process a (python) network object into config Attrdict.
    :param subnet object: python subnet object from the netobj queue
    :return config dict: Attrdict of JSON config fragments
    """
    pass
