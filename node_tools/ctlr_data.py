# coding: utf-8

"""
    Default fpn ctlr state variables.  Trie keys must be in the set
    `string.hexdigits`.
    :var net_trie: <Trie> of JSON network/member data objects
    :var id_trie: <Trie> of JSON member node net_id state objects
    :var rules: <cfg_dict> default flow rules for each network link
"""
import string

import datrie


net_trie = datrie.Trie(string.hexdigits)
id_trie = datrie.Trie(string.hexdigits)

rules = {
    'rules': [
        {
            'type': 'MATCH_ETHERTYPE',
            'not': True,
            'or': False,
            'etherType': 2048
        },
        {
            'type': 'MATCH_ETHERTYPE',
            'not': True,
            'or': False,
            'etherType': 2054
        },
        {
            'type': 'ACTION_DROP'
        },
        {
            'type': 'MATCH_IP_PROTOCOL',
            'not': False,
            'or': False,
            'ipProtocol': 6
        },
        {
            'type': 'MATCH_IP_DEST_PORT_RANGE',
            'not': False,
            'or': False,
            'start': 80,
            'end': 80
        },
        {
            'type': 'MATCH_IP_DEST_PORT_RANGE',
            'not': False,
            'or': True,
            'start': 443,
            'end': 443
        },
        {
            'type': 'ACTION_ACCEPT'
        },
        {
            'type': 'MATCH_CHARACTERISTICS',
            'not': False,
            'or': False,
            'mask': '0000000000000002'
        },
        {
            'type': 'MATCH_CHARACTERISTICS',
            'not': True,
            'or': False,
            'mask': '0000000000000010'
        },
        {
            'type': 'ACTION_BREAK'
        },
        {
            'type': 'MATCH_IP_PROTOCOL',
            'not': False,
            'or': False,
            'ipProtocol': 1
        },
        {
            'type': 'ACTION_ACCEPT'
        },
        {
            'type': 'MATCH_IP_PROTOCOL',
            'not': False,
            'or': False,
            'ipProtocol': 2
        },
        {
            'type': 'ACTION_ACCEPT'
        },
        {
            'type': 'ACTION_ACCEPT'
        }
    ]
}
