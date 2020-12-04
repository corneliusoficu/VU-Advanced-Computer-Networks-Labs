# Copyright 2020 Lin Wang

# This code is part of the Advanced Computer Networks (ACN) course at VU 
# Amsterdam.

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

#!/usr/bin/env python3

# A dirty workaround to import topo.py from lab2

import os
import subprocess
import time

import mininet
import mininet.clean
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import lg, info
from mininet.link import TCLink
from mininet.node import Node, OVSKernelSwitch, RemoteController
from mininet.topo import Topo
from mininet.util import waitListening, custom

import topo


class FattreeNet(Topo):
	"""
	Create a fat-tree network in Mininet
	"""

	def __init__(self, ft_topo):
		Topo.__init__(self)
		self.servers = {node.id: self.addHost(node.id, ip=node.ip_address) for node in ft_topo.servers}
		self.core_switches = {switch.id: self.addSwitch(switch.id) for switch in ft_topo.core_switches}
		self.aggregation_switches = {switch.id: self.addSwitch(switch.id) for switch in ft_topo.agg_switches}
		self.edge_switches = {switch.id: self.addSwitch(switch.id) for switch in ft_topo.edge_switches}
		self.ft_nodes = {**self.servers, **self.core_switches, **self.aggregation_switches, **self.edge_switches}

		print(f'Number of core switches: {len(self.core_switches)}')
		print(f'Number of aggregation switches: {len(self.aggregation_switches)}')
		print(f'Number of edge switches: {len(self.edge_switches)}')
		print(f'Number of servers: {len(self.servers)}')

		link_opts = dict(cls=TCLink, bw=15, delay='5ms')

		self.all_nodes = ft_topo.servers + ft_topo.core_switches + ft_topo.agg_switches + ft_topo.edge_switches
		self.ft_links = {(edge.left_node.id, edge.right_node.id) for node in self.all_nodes for edge in node.edges}
		self.ft_links = [self.addLink(self.ft_nodes[a], self.ft_nodes[b], **link_opts) for (a, b) in self.ft_links]


def make_mininet_instance(graph_topo):
	net_topo = FattreeNet(graph_topo)
	net = Mininet(topo=net_topo, controller=None, autoSetMacs=True)
	net.addController('c0', controller=RemoteController, ip="127.0.0.1", port=6653)
	return net


def run(graph_topo):
	
	# Run the Mininet CLI with a given topology
	lg.setLogLevel('info')
	mininet.clean.cleanup()
	net = make_mininet_instance(graph_topo)

	info('*** Starting network ***\n')
	net.start()
	info('*** Running CLI ***\n')
	script = 'performence.sh'
	CLI(net, script=script)
	CLI(net)
	info('*** Stopping network ***\n')
	net.stop()


ft_topo = topo.Fattree(4)
run(ft_topo)