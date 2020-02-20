# coding: utf-8

"""
    Default fpn ctlr state variables.
    :var mbr_data:
    :var net_data:
    :var net_trie: a Trie of JSON state objects
"""
import string

import datrie


mbr_data = {
    "authorized": False,
    "capabilities": [],
    "id": None,
    "identity": None,
    "ipAssignments": [],
    "noAutoAssignIps": False,
    "nwid": None,
    "objtype": None,
    "tags": []
}

net_data = {
  "capabilities": [],
  "id": None,
  "ipAssignmentPools": [],
  "nwid": None,
  "objtype": None,
  "private": True,
  "routes": [],
  "tags": [],
  "v4AssignMode": {
    "zt": True
  }
}

net_trie = datrie.Trie(string.hexdigits)
