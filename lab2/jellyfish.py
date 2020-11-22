import random

from topo import Node, generate_random_regular_graph_edges, draw_topology, NetworkError


class Jellyfish:

    def __init__(self, num_servers, num_switches, num_ports, seed_value):
        self.servers = []
        self.switches = []
        self.num_servers = num_servers
        self.num_switches = num_switches
        self.num_ports = num_ports
        self.generate(seed_value)

    def generate(self, seed_value):
        seed = random.Random(seed_value)
        self.switches = list(map(lambda index: Node("sw"+str(index), "sw"), range(self.num_switches)))

        ports_for_switches = int(self.num_ports/2)
        if ports_for_switches % 2 != 0:
            ports_for_switches = ports_for_switches + 1

        switch_edges = generate_random_regular_graph_edges(ports_for_switches, self.num_switches, seed=seed)
        self._interconnect_switches_based_on_edges(switch_edges)
        self.servers = list(map(lambda index: Node("sv"+str(index), "sv"), range(self.num_servers)))
        self._attach_servers_to_switches()

    def _interconnect_switches_based_on_edges(self, switch_edges):
        for switch_edge in switch_edges:
            left_node = self.switches[switch_edge[0]]
            right_node = self.switches[switch_edge[1]]
            left_node.add_edge(right_node, 1)

    def _attach_servers_to_switches(self):
        for server in self.servers:
            switch = self._find_switch_index_with_empty_port()
            switch.add_edge(server, 1)

    def _find_switch_index_with_empty_port(self):
        switch_with_no_servers_connected = self._get_first_switch_with_no_connected_servers()

        if switch_with_no_servers_connected is not None:
            return switch_with_no_servers_connected

        for switch in self.switches:
            if len(switch.edges) < self.num_ports:
                return switch

        raise NetworkError("Server could not be attached to a switch. There might be too many servers for the existing"
                           " ports")

    def _get_first_switch_with_no_connected_servers(self):
        for switch in self.switches:
            if len(switch.edges) == self.num_ports:
                continue

            switch_has_server_attached = False
            for edge in switch.edges:
                if edge.rnode.type == 'sv':
                    switch_has_server_attached = True
                    break

            if not switch_has_server_attached:
                return switch

        return None


if __name__ == '__main__':
    random_value = random.randint(0, 300)
    jellyfish = Jellyfish(80, 21, 8, random_value)
    draw_topology(jellyfish.switches)