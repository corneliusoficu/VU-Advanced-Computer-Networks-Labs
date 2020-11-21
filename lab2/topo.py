# Copyright 2020 Lin Wang

# This code is part of the Advanced Computer Networks (2020) course at Vrije
# Universiteit Amsterdam.

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys
import random
import queue

# Class for an edge in the graph
class Edge:
	def __init__(self):
		self.lnode = None
		self.rnode = None
		self.bw = None

	def remove(self):
		self.lnode.edges.remove(self)
		self.rnode.edges.remove(self)
		self.lnode = None
		self.rnode = None
		self.bw = None

	def __str__(self):
		return self.lnode.id + '->' + self.rnode.id + ' - BW:' + str(self.bw)

# Class for a node in the graph
class Node:
	def __init__(self, id, type):
		self.edges = []
		self.id = id
		self.type = type

	# Add an edge connected to another node
	def add_edge(self, node, bw):
		edge = Edge()
		edge.lnode = self
		edge.rnode = node
		edge.bw = bw
		self.edges.append(edge)
		node.edges.append(edge)
		return edge

	# Remove an edge from the node
	def remove_edge(self, edge):
		self.edges.remove(edge)

	# Decide if another node is a neighbor
	def is_neighbor(self, node):
		for edge in self.edges:
			if edge.lnode == node or edge.rnode == node:
				return True
		return False


# class Jellyfish:
#
# 	def __init__(self, num_servers, num_switches, num_ports):
# 		self.servers = []
# 		self.switches = []
# 		self.generate(num_servers, num_switches, num_ports)
#
# 	def generate(self, num_servers, num_switches, num_ports):
#
# 		# TODO: code for generating the jellyfish topology

class Fattree:

	CoreSwitches = []
	AggSwitches = []
	EdgeSwitches = []
	Servers = []

	def __init__(self, num_ports):
		self.pod = num_ports
		self.numCore = (num_ports // 2) ** 2
		self.numAgg = (num_ports ** 2) // 2
		self.numEdge = (num_ports ** 2) // 2
		self.density = num_ports // 2
		self.numSv = (num_ports ** 3 ) // 4
		self.bw_c2a = 0.2
		self.bw_a2e = 0.1
		self.bw_e2s = 0.05

		print(f'\nGenerating Fattree with {num_ports} ports on each switch..')
		print("Switch Level 1 = Core Layer Switch")
		print("Switch Level 2 = Aggregation Layer Switch")
		print("Switch Level 3 = Edge Layer Switch")
		self.generateTopo(num_ports)
		self.generateLinks(bw_c2a = self.bw_c2a, bw_a2e = self.bw_a2e, bw_e2s = self.bw_e2s)

	def generateTopo(self, num_ports):
		self.createCore(self.numCore)
		self.createAgg(self.numAgg)
		self.createEdge(self.numEdge)
		self.createServer(self.numSv)
		self.printTopo()

	def addSwitch(self, num_sw, level, switchList):
		for sw in range(1, num_sw + 1):
			switchList.append(Node('sw' + str(level) + str(sw), 'Switch Level ' + str(level)))

	def createCore(self, num_sw):
		print("\nCreating Core Layer..")
		self.addSwitch(num_sw, 1, self.CoreSwitches)

	def createAgg(self, num_sw):
		print("Creating Aggregation Layer..")
		self.addSwitch(num_sw, 2, self.AggSwitches)

	def createEdge(self, num_sw):
		print("Creating Edge Layer..\n")
		self.addSwitch(num_sw, 3, self.EdgeSwitches)

	def createServer(self, num_sv):
		for sv in range(1, num_sv + 1):
			self.Servers.append(Node('sv'+ str(sv),'Server'))

	#GENERATING LINKS
	def generateLinks(self, bw_c2a = 0.2, bw_a2e = 0.1, bw_e2s = 0.05):
		print('\nAdding links from core switches to aggregation switches..')
		step = self.pod // 2
		for x in range (0, self.numAgg, step):
			for y in range(0, step):
				for z in range(0, step):
					self.CoreSwitches[y*step+z].add_edge(self.AggSwitches[x+y], bw_c2a)

		print('Adding links from aggregation switches to edge switches..')
		for x in range (0, self.numAgg, step):
			for y in range(0, step):
				for z in range(0, step):
					self.AggSwitches[x+y].add_edge(self.EdgeSwitches[x+z], bw_a2e)

		print('Adding links from edge switches to servers..')
		for x in range(0, self.numEdge):
			for y in range (0, self.density):
				self.EdgeSwitches[x].add_edge(self.Servers[self.density * x + y], bw_e2s)
		self.printLinks()

	def printTopo(self):
		print ('Printing core switches...')
		for x in self.CoreSwitches:
			print (f'ID: {x.id} TYPE: {x.type}')

		print ('\nPrinting aggregation switches...')
		for x in self.AggSwitches:
			print (f'ID: {x.id} TYPE: {x.type}')

		print ('\nPrinting edge switches...')
		for x in self.EdgeSwitches:
			print (f'ID: {x.id} TYPE: {x.type}')

		print ('\nPrinting generated servers...')
		for x in self.Servers:
			print (f'ID: {x.id} TYPE: {x.type}')

	def printLinks(self):
		print('\nPrinting links for core nodes..\n')
		for sw in self.CoreSwitches:
			print(f'Links for core switch {self.CoreSwitches.index(sw) + 1}:')
			for x in sw.edges:
				print(x)

		print('\nLinks for aggregation nodes..\n')
		for sw in self.AggSwitches:
			print(f'Links for aggregation switch {self.AggSwitches.index(sw) + 1}:')
			for x in sw.edges:
				print(x)

		print('\nPrinting links for edges nodes..\n')
		for sw in self.EdgeSwitches:
			print(f'Links for edge switch {self.EdgeSwitches.index(sw) + 1}:')
			for x in sw.edges:
				print(x)

		print('\nPrinting links for server nodes..\n')
		for sv in self.Servers:
			print(f'Links for server {self.Servers.index(sv) + 1}:')
			for x in sv.edges:
				print(x)

#Building Fattree with 8 switch ports
tree = Fattree(4)
