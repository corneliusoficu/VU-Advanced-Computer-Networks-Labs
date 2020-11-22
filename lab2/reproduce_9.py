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
import random
from itertools import count
import matplotlib.pyplot as plt

import topo
import jellyfish
import reproduce_1c
from heapq import heappush, heappop
from multiprocessing import Pool, Process, Queue
K = 8


def topo_edge_iter_for_node(topo, node):
    if node in topo:
        return [(node, dest) for dest in topo[node]]
    return []


def topo_has_edge(topo, left_node, right_node):
    if right_node in topo[left_node] or left_node in topo[right_node]:
        return True
    return False


def topo_remove_edge(topo, left_node, right_node):
    topo[left_node].remove(right_node)
    topo[right_node].remove(left_node)


def topo_add_edge(topo, left_node, right_node):
    topo.setdefault(left_node, []).append(right_node)
    topo.setdefault(right_node, []).append(left_node)


def lee_algorithm_multiple_paths(k, paths_to_calculate, topo, queue):
    all_paths = {}

    for start_node, end_node in paths_to_calculate:
        lengths, paths = lee_algorithm_k_shorthest_paths(k, topo, start_node, end_node)
        all_paths[(start_node, end_node)] = paths

    queue.put(all_paths)


def lee_algorithm_k_shorthest_paths(k, topo, start_node, end_node):
    if start_node == end_node:
        return [0], [[start_node]]

    path = reproduce_1c.bfs_shortest_path(topo, start_node, end_node)
    lengths = [len(path) - 1]
    paths = [path]
    c = count()
    B = []

    for i in range(1, k):
        for j in range(len(paths[-1]) - 1):
            spur_node = paths[-1][j]
            root_path = paths[-1][:j+1]

            edges_removed = []
            for c_path in paths:
                if len(c_path) > j and root_path == c_path[:j+1]:
                    u = c_path[j]
                    v = c_path[j + 1]
                    if topo_has_edge(topo, u, v):
                        topo_remove_edge(topo, u, v)
                        edges_removed.append((u, v))

            for n in range(len(root_path) - 1):
                node = root_path[n]
                for (u, v) in topo_edge_iter_for_node(topo, node):
                    topo_remove_edge(topo, u, v)
                    edges_removed.append((u, v))

            spur_path = reproduce_1c.bfs_shortest_path(topo, spur_node, end_node)
            if spur_path and end_node in spur_path:
                total_path = root_path[:-1] + spur_path
                total_path_length = len(total_path) - 1
                heappush(B, (total_path_length, next(c), total_path))

            for e in edges_removed:
                u, v = e
                topo_add_edge(topo, u, v)

        if B:
            (l, _, p) = heappop(B)
            lengths.append(l)
            paths.append(p)
        else:
            break

    return lengths, paths


def chunk_array(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out


def random_derangement(n):
    while True:
        v = list(range(n))
        for j in range(n - 1, -1, -1):
            p = random.randint(0, j)
            if v[p] == j:
                break
            else:
                v[j], v[p] = v[p], v[j]
        else:
            if v[0] != 0:
                return tuple(v)


def compute_all_k_shortest_paths(k, topo, parallelism, server_pairs):
    topo_copy = topo.copy()
    chunks = chunk_array(server_pairs, parallelism)

    processes = []
    for i in range(0, parallelism):
        q = Queue()
        p = Process(target=lee_algorithm_multiple_paths, args=(k, chunks[i], topo_copy, q))
        p.start()
        processes.append((p, q))

    all_ksp = {}
    for p, q in processes:
        p.join()
        computed_dict = q.get()
        print(f'Computed ksp dict of size: {len(computed_dict)}')
        all_ksp.update(computed_dict)

    return all_ksp


def topo_get_all_links(topo):
    return [(node_1, node_2) for node_1, edges in topo.items() for node_2 in edges]


def get_path_counts(all_ksp, traffic_matrix, all_links, all_servers):
    counts = {}
    print(len(all_links))
    for link in all_links:
        a, b = link
        counts[(a, b)] = {'8-ksp': 0}

    for start_host in range(len(traffic_matrix)):
        dest_host = traffic_matrix[start_host]

        start_node = all_servers[start_host].id
        dest_node = all_servers[dest_host].id

        if start_node == dest_node:
            continue

        if (start_node, dest_node) in all_ksp:
            ksp = all_ksp[(start_node, dest_node)]
        else:
            ksp = all_ksp[(dest_node, start_node)]

        for path in ksp:
            prev_node = None
            for node in path:
                if not prev_node:
                    prev_node = node
                    continue
                link = (prev_node, node)
                counts[link]["8-ksp"] += 1
                prev_node = node

    return counts


def assemble_histogram(path_counts):
    ksp_distinct_paths_counts = []

    for _, value in sorted(path_counts.items(), key=lambda kv: (kv[1]["8-ksp"], kv[0])):
        ksp_distinct_paths_counts.append(value["8-ksp"])

    x = range(len(ksp_distinct_paths_counts))
    fig = plt.figure(figsize=(11, 8))
    ax1 = fig.add_subplot(111)

    ax1.plot(x, ksp_distinct_paths_counts, color='b', label="8 Shortest Paths")
    plt.legend(loc="upper left")
    ax1.set_xlabel("Rank of Link")
    ax1.set_ylabel("# of Distinct Paths Link is on")
    plt.show()


if __name__ == '__main__':
    args = reproduce_1c.parse_args()
    jf_topo = jellyfish.Jellyfish(args.servers, args.switches, args.ports, 45)
    all_nodes = jf_topo.switches + jf_topo.servers

    derangement = random_derangement(685)
    derangment_links = []

    for start_host in derangement:
        dest_host = derangement[start_host]

        start_node = jf_topo.servers[start_host].id
        dest_node = jf_topo.servers[dest_host].id

        derangment_links.append((start_node, dest_node))

    parallelism = 40
    topo = reproduce_1c.generate_tree_adj(all_nodes)
    all_ksp = compute_all_k_shortest_paths(K, topo, parallelism, derangment_links)
    all_links = topo_get_all_links(topo)

    path_counts = get_path_counts(all_ksp, derangement, all_links, jf_topo.servers)
    assemble_histogram(path_counts)

