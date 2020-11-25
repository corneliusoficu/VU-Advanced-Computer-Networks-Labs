class NetworkError(Exception):
    def __init__(self, message):
        super(NetworkError, self).__init__(message)


# Class for an edge in the graph
class Edge:
    def __init__(self):
        self.left_node = None
        self.right_node = None
        self.bw = None

    def remove(self):
        self.left_node.edges.remove(self)
        self.right_node.edges.remove(self)
        self.left_node = None
        self.right_node = None
        self.bw = None

    def __str__(self):
        return self.left_node.id + '->' + self.right_node.id + ' - BW:' + str(self.bw)


# Class for a node in the graph
class Node:
    def __init__(self, id, type, ip_address):
        self.edges = []
        self.id = id
        self.type = type
        self.ip_address = ip_address

    # Add an edge connected to another node
    def add_edge(self, node, bw):
        edge = Edge()
        edge.left_node = self
        edge.right_node = node
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

    def __str__(self) -> str:
        return f'{self.id} {self.ip_address}'


class Fattree:
    core_switches = []
    agg_switches = []
    edge_switches = []
    servers = []

    def __init__(self, num_ports):
        self.num_ports = num_ports
        self.num_pods = num_ports
        self.num_core = (num_ports // 2) ** 2
        self.num_agg = (num_ports ** 2) // 2
        self.num_edge = (num_ports ** 2) // 2
        self.density = num_ports // 2
        self.num_sv = (num_ports ** 3) // 4
        self.bw_c2a = 0.2
        self.bw_a2e = 0.1
        self.bw_e2s = 0.05

        print(f'\nGenerating Fattree with {num_ports} ports on each switch..')
        print("Switch Level 1 = Core Layer Switch")
        print("Switch Level 2 = Aggregation Layer Switch")
        print("Switch Level 3 = Edge Layer Switch")
        self._generate_topo(num_ports)
        self._generate_links(bw_c2a=self.bw_c2a, bw_a2e=self.bw_a2e, bw_e2s=self.bw_e2s)

    def _generate_topo(self, num_ports):
        self._create_core(self.num_core)
        self._create_agg(self.num_agg)
        self._create_edge(self.num_edge)
        self._create_server(self.num_sv)

    def _core_switches_ip_addressing_scheme(self, sw_index):
        half_ports = self.num_ports / 2
        j = int(((sw_index - (sw_index % half_ports)) + half_ports) / half_ports)
        i = int(sw_index % half_ports + 1)
        ip_address = f'10.{self.num_ports}.{j}.{i}'
        return ip_address

    def _agg_switches_ip_addressing_scheme(self, sw_index):
        half_ports = self.num_ports / 2
        pod_index = int(((sw_index - (sw_index % half_ports)) + half_ports) / half_ports) - 1
        agg_switch_index = int(half_ports + (sw_index % half_ports))
        return f'10.{pod_index}.{agg_switch_index}.1'

    def _edge_switches_ip_addressing_scheme(self, sw_index):
        half_ports = self.num_ports / 2
        pod_index = int(((sw_index - (sw_index % half_ports)) + half_ports) / half_ports) - 1
        edge_switch_index = int(sw_index % half_ports)
        return f'10.{pod_index}.{edge_switch_index}.1'

    def _server_ip_addressing_scheme(self, sv_index):
        pod_index = int(((sv_index - (sv_index % self.num_pods)) + self.num_pods) / self.num_pods) - 1
        half_ports = self.num_ports / 2
        switch_index = int(((sv_index - (sv_index % half_ports)) + half_ports) / half_ports) - 1
        id = 2 + int(sv_index % (self.num_ports / 2))
        return f'10.{pod_index}.{switch_index}.{id}'

    def _add_switch(self, num_sw, level, switch_list, addressing_scheme):
        for sw in range(0, num_sw):
            ip_address = addressing_scheme(sw)
            switch = Node('sw' + str(level) + str(sw+1), 'Switch Level ' + str(level), ip_address)
            switch_list.append(switch)
            print(switch)

    def _create_core(self, num_sw):
        print("\nCreating Core Layer..")
        self._add_switch(num_sw, 1, self.core_switches, self._core_switches_ip_addressing_scheme)

    def _create_agg(self, num_sw):
        print("Creating Aggregation Layer..")
        self._add_switch(num_sw, 2, self.agg_switches, self._agg_switches_ip_addressing_scheme)

    def _create_edge(self, num_sw):
        print("Creating Edge Layer..\n")
        self._add_switch(num_sw, 3, self.edge_switches, self._edge_switches_ip_addressing_scheme)

    def _create_server(self, num_sv):
        print("Creating Server Layer..\n")
        for sv in range(0, num_sv):
            ip_address = self._server_ip_addressing_scheme(sv)
            server = Node('sv' + str(sv+1), 'Server', ip_address)
            self.servers.append(server)
            print(server)

    def _generate_links(self, bw_c2a=0.2, bw_a2e=0.1, bw_e2s=0.05):
        print('\nAdding links from core switches to aggregation switches..')
        step = self.num_pods // 2
        for x in range(0, self.num_agg, step):
            for y in range(0, step):
                for z in range(0, step):
                    self.core_switches[y * step + z].add_edge(self.agg_switches[x + y], bw_c2a)

        print('Adding links from aggregation switches to edge switches..')
        for x in range(0, self.num_agg, step):
            for y in range(0, step):
                for z in range(0, step):
                    self.agg_switches[x + y].add_edge(self.edge_switches[x + z], bw_a2e)

        print('Adding links from edge switches to servers..')
        for x in range(0, self.num_edge):
            for y in range(0, self.density):
                self.edge_switches[x].add_edge(self.servers[self.density * x + y], bw_e2s)


if __name__ == '__main__':
    topology = Fattree(4)

