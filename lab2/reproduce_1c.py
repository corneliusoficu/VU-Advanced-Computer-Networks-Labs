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

import topo
import matplotlib.pyplot as plt

# Same setup for Jellyfish and Fattree
num_servers = 686
num_switches = 245
num_ports = 14

ft_topo = topo.Fattree(num_ports)
#jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)

# TODO: code for reproducing Figure 1(c) in the jellyfish paper

############################################FATTREE##############################################
def generate_ft_adj():
    allNodes = ft_topo.CoreSwitches + ft_topo.AggSwitches + ft_topo.EdgeSwitches + ft_topo.Servers
    nodeDict = {}
    for node in allNodes:
        neighbours = []
        for edge in node.edges:
            if edge.lnode.id != node.id:
                neighbours.append(edge.lnode.id)
            else:
                neighbours.append(edge.rnode.id)
        nodeDict[node.id] = neighbours
    return nodeDict

def bfs_shortest_path(topo, startNode, endNode):
    exploredNodes = []
    nodesQueue = [[startNode]]
    while nodesQueue:
        path = nodesQueue.pop(0)
        node = path[-1]
        if node not in exploredNodes:
            neighbours = topo[node]
            for neighbour in neighbours:
                newPath = list(path)
                newPath.append(neighbour)
                nodesQueue.append(newPath)
                if neighbour == endNode:
                    return newPath
            exploredNodes.append(node)

def compute_results(nodeDict):
    servers = []
    for node in nodeDict:
        if node.startswith('sv'):
            servers.append(node)
    pathsLength = []
    for x in range(0, len(servers) - 1):
        for y in range(x+1, len(servers)):
            #print(f'From node {servers[x]} to {servers[y]} - {bfs_shortest_path(nodeDict, servers[x], servers[y])}')
            pathsLength.append(len(bfs_shortest_path(nodeDict, servers[x], servers[y])) - 1)

    #designed for 14-ports switches
    possiblePairs = 234955

    #print the results
    pathsOf2 = pathsLength.count(2)
    print(f'\nThere are {pathsOf2} 2-paths ({round((pathsOf2 / possiblePairs) * 100, 2)}% of total paths)!')
    pathsOf3 = pathsLength.count(3)
    print(f'There are {pathsOf3} 3-paths ({round((pathsOf3 / possiblePairs) * 100, 2)}% of total paths)!')
    pathsOf4 = pathsLength.count(4)
    print(f'There are {pathsOf4} 4-paths ({round((pathsOf4 / possiblePairs) * 100, 2)}% of total paths)!')
    pathsOf5 = pathsLength.count(5)
    print(f'There are {pathsOf4} 5-paths ({round((pathsOf5 / possiblePairs) * 100, 2)}% of total paths)!')
    pathsOf6 = pathsLength.count(6)
    print(f'There are {pathsOf6} 6-paths ({round((pathsOf6 / possiblePairs) * 100, 2)}% of total paths)!')

    #plot the results
    names = ['2', '3', '4', '5', '6']
    values = [pathsOf2 / possiblePairs, pathsOf3 / possiblePairs, pathsOf4 / possiblePairs, pathsOf5 / possiblePairs, pathsOf6 / possiblePairs]
    plt.figure(figsize=(10,4))
    plt.subplot(131)
    plt.bar(names,values)
    plt.ylim([0,1])
    plt.ylabel('Fraction of server pairs')
    plt.xlabel('Paths length')
    plt.suptitle('Path length distribution between servers for a 686-server Fattree')
    plt.grid(True)
    plt.show()

nodeDict = generate_ft_adj()
compute_results(nodeDict)
##################################################################################################
