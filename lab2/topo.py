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
import networkx as nx
# importing matplotlib.pyplot
import matplotlib.pyplot as plt

from collections import defaultdict


class NetworkError(Exception):
    def __init__(self, message):
        super(NetworkError, self).__init__(message)


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


def generate_random_regular_graph_edges(node_degree, number_of_nodes, seed=None):
    if (number_of_nodes * node_degree) % 2 != 0:
        raise NetworkError("n * d must be even")

    if not 0 <= node_degree < number_of_nodes:
        raise NetworkError("the 0 <= d < n inequality must be satisfied")

    if node_degree == 0:
        return []

    def _suitable(edges, potential_edges):
        # Helper subroutine to check if there are suitable edges remaining
        # If False, the generation of the graph has failed
        if not potential_edges:
            return True
        for s1 in potential_edges:
            for s2 in potential_edges:
                # Two iterators on the same dictionary are guaranteed
                # to visit it in the same order if there are no
                # intervening modifications.
                if s1 == s2:
                    # Only need to consider s1-s2 pair one time
                    break
                if s1 > s2:
                    s1, s2 = s2, s1
                if (s1, s2) not in edges:
                    return True
        return False

    def _try_creation():
        # Attempt to create an edge set

        edges = set()
        stubs = list(range(number_of_nodes)) * node_degree

        while stubs:
            potential_edges = defaultdict(lambda: 0)
            seed.shuffle(stubs)
            stub_iter = iter(stubs)

            for s1, s2 in zip(stub_iter, stub_iter):
                if s1 > s2:
                    s1, s2 = s2, s1
                if s1 != s2 and ((s1, s2) not in edges):
                    edges.add((s1, s2))
                else:
                    potential_edges[s1] += 1
                    potential_edges[s2] += 1

            if not _suitable(edges, potential_edges):
                return None  # failed to find suitable edge set

            stubs = [
                node
                for node, potential in potential_edges.items()
                for _ in range(potential)
            ]
        return edges

    # Even though a suitable edge set exists,
    # the generation of such a set is not guaranteed.
    # Try repeatedly to find one.
    edges = _try_creation()
    while edges is None:
        edges = _try_creation()

    return edges


def draw_topology(nodes):
    g = nx.Graph()
    for node in nodes:
        for edge in node.edges:
            g.add_edge(edge.lnode.id, edge.rnode.id)

    nx.draw(g, with_labels=True)
    plt.show()



