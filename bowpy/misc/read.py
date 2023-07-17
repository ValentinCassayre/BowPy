from __future__ import absolute_import
import numpy as np
import scipy as sp
import obspy
from obspy.clients.fdsn import Client
from obspy import UTCDateTime, Stream, Inventory, Trace, read
from obspy.core.inventory.network import Network

from bowpy.util.base import cat4stream, inv4stream
from nmpy.util.base import read_ahx
from bowpy.util.array_util import attach_network_to_traces, attach_coordinates_to_traces
import warnings


def read_st(input, format=None, network=None, client_name=None):

    try:
        stream = read(input, format)
    except UnicodeDecodeError:
        stream = read_ahx(input)

    try:
        if stream[0].stats._format == "Q":
            for i, trace in enumerate(stream):
                stream[i].stats.distance = trace.stats.sh["DISTANCE"]
                stream[i].stats.depth = trace.stats.sh["DEPTH"]
                stream[i].stats.origin = trace.stats.sh["ORIGIN"]
    except:
        msg = "No Q-file"

    if isinstance(network, str):
        if isinstance(client_name, str):
            try:
                cat = cat4stream(stream, client_name)
                inv = inv4stream(stream, network, client_name)

                attach_coordinates_to_traces(stream, inv, cat[0])
                attach_network_to_traces(stream, inv)
                print("Stream input with Meta-Information read.")
                return stream
            except:
                msg = "Error with Input: network or client_name wrong?"
                raise IOError(msg)
    else:
        print("Stream input without Meta-Information read.")
        return stream
