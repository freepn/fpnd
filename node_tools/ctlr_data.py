# coding: utf-8

"""
    Default fpn ctlr state variables.
    :var net_trie: a Trie of JSON network/member state objects
    :var id_trie: a Trie of JSON member node net_id objects
"""
import string

import datrie


net_trie = datrie.Trie(string.hexdigits)
id_trie = datrie.Trie(string.hexdigits)
