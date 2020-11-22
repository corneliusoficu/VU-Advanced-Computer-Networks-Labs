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
import argparse
import random
import time
from functools import partial

import fat_tree
import matplotlib.pyplot as plt
import numpy as np

# Same setup for Jellyfish and Fattree
import jellyfish

from multiprocessing import Pool, Process, Manager

#jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)

# TODO: code for reproducing Figure 1(c) in the jellyfish paper

############################################FATTREE##############################################
def generate_tree_adj(allNodes):
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
    possiblePairs = len(pathsLength)
    print(f'\nThere are {possiblePairs} paths in total')

    #print the results
    pathsOf2 = pathsLength.count(2)
    print(f'There are {pathsOf2} 2-paths ({round((pathsOf2 / possiblePairs) * 100, 2)}% of total paths)!')
    pathsOf3 = pathsLength.count(3)
    print(f'There are {pathsOf3} 3-paths ({round((pathsOf3 / possiblePairs) * 100, 2)}% of total paths)!')
    pathsOf4 = pathsLength.count(4)
    print(f'There are {pathsOf4} 4-paths ({round((pathsOf4 / possiblePairs) * 100, 2)}% of total paths)!')
    pathsOf5 = pathsLength.count(5)
    print(f'There are {pathsOf5} 5-paths ({round((pathsOf5 / possiblePairs) * 100, 2)}% of total paths)!')
    pathsOf6 = pathsLength.count(6)
    print(f'There are {pathsOf6} 6-paths ({round((pathsOf6 / possiblePairs) * 100, 2)}% of total paths)!')

    values = [pathsOf2 / possiblePairs, pathsOf3 / possiblePairs, pathsOf4 / possiblePairs, pathsOf5 / possiblePairs,
              pathsOf6 / possiblePairs]
    return values


def plot_results(topo_1_values, topo_2_values):
    #plot the results
    labels = ['2', '3', '4', '5', '6']

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots(figsize=(10, 5))
    rects1 = ax.bar(x - width / 2, topo_2_values, width, label='Jellyfish', color='b')
    rects2 = ax.bar(x + width / 2, topo_1_values, width, label='Fat Tree', color='r')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    plt.ylim([0, 1])
    ax.set_ylabel('Fraction of server pairs')
    ax.set_xlabel('Paths length')
    ax.set_title('Path length distribution between servers for a 686-server Fattree and Jellyfish Topology')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = float('%.2f' % rect.get_height())
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()

    plt.show()


def generate_1c_fat_tree(nr_ports, shared_list):
    ft_topo = fat_tree.Fattree(nr_ports)
    allNodes = ft_topo.CoreSwitches + ft_topo.AggSwitches + ft_topo.EdgeSwitches + ft_topo.Servers
    nodeDict = generate_tree_adj(allNodes)
    results = compute_results(nodeDict)
    shared_list.extend(results)


def generate_1c_jellyfish(nr_servers, nr_switches, nr_ports, seed_value):
    print(nr_servers, nr_switches, nr_ports, seed_value)
    jf_topo = jellyfish.Jellyfish(nr_servers, nr_switches, nr_ports, seed_value)
    allNodes = jf_topo.switches + jf_topo.servers
    nodeDict = generate_tree_adj(allNodes)
    return compute_results(nodeDict)


def parse_args():
    parser = argparse.ArgumentParser(description='Reproduce figure 1c of paper')

    parser.add_argument('-s', '--servers', dest='servers', required=True, type=int,
                        help='Number of servers for the experiment')

    parser.add_argument('-sw', '--switches', dest='switches', required=True, type=int,
                        help='Number of switches for the experiment')

    parser.add_argument('-p', '--ports', dest='ports', required=True, type=int,
                        help='Number of ports for the experiment')

    parser.add_argument('-r', '--repetitions', dest='repetitions', required=True, type=int,
                        help='Number of repetitions for the jellyfish experiment')

    return parser.parse_args()


if __name__ == '__main__':
    start_time = time.time()

    args = parse_args()
    print(f'Reproducing figure 1c for the following configuration: Servers: {args.servers}, Switches: {args.switches}, '
          f'Ports: {args.ports}, Jellyfish repetitions: {args.repetitions}')

    manager = Manager()
    ft_results_list = manager.list()

    ft_process = Process(target=generate_1c_fat_tree, args=(args.ports, ft_results_list))
    ft_process.start()

    seed_values = [random.randint(0, 300) for _ in range(0, args.repetitions)]
    jellyfish_args = [(args.servers, args.switches, args.ports, seed_value) for seed_value in seed_values]

    with Pool(args.repetitions) as p:
        results_multiple_runs_jellyfish = p.starmap(generate_1c_jellyfish, jellyfish_args)

    average_jellyfish_results = list(map(lambda x: x / args.repetitions, [sum(x) for x in zip(*results_multiple_runs_jellyfish)]))

    ft_process.join()
    end_time = time.time()
    print(f"Total duration: {end_time-start_time} seconds")
    plot_results(ft_results_list, average_jellyfish_results)




