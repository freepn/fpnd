# coding: utf-8

"""
    Default fpn ctlr state variables.  Trie keys must be in the set
    `string.hexdigits`.
    :var net_trie: a Trie of JSON network/member data objects
    :var id_trie: a Trie of JSON member node net_id state objects
"""
import string

import datrie


net_trie = datrie.Trie(string.hexdigits)
id_trie = datrie.Trie(string.hexdigits)
