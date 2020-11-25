from topo import Node, draw_topology


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
        self.numSv = (num_ports ** 3) // 4
        self.bw_c2a = 0.2
        self.bw_a2e = 0.1
        self.bw_e2s = 0.05

        print(f'\nGenerating Fattree with {num_ports} ports on each switch..')
        print("Switch Level 1 = Core Layer Switch")
        print("Switch Level 2 = Aggregation Layer Switch")
        print("Switch Level 3 = Edge Layer Switch")
        self.generateTopo(num_ports)
        self.generateLinks(bw_c2a=self.bw_c2a, bw_a2e=self.bw_a2e, bw_e2s=self.bw_e2s)

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
            self.Servers.append(Node('sv' + str(sv), 'Server'))

    # GENERATING LINKS
    def generateLinks(self, bw_c2a=0.2, bw_a2e=0.1, bw_e2s=0.05):
        print('\nAdding links from core switches to aggregation switches..')
        step = self.pod // 2
        for x in range(0, self.numAgg, step):
            for y in range(0, step):
                for z in range(0, step):
                    self.CoreSwitches[y * step + z].add_edge(self.AggSwitches[x + y], bw_c2a)

        print('Adding links from aggregation switches to edge switches..')
        for x in range(0, self.numAgg, step):
            for y in range(0, step):
                for z in range(0, step):
                    self.AggSwitches[x + y].add_edge(self.EdgeSwitches[x + z], bw_a2e)

        print('Adding links from edge switches to servers..')
        for x in range(0, self.numEdge):
            for y in range(0, self.density):
                self.EdgeSwitches[x].add_edge(self.Servers[self.density * x + y], bw_e2s)
        self.printLinks()

    def printTopo(self):
        print('Printing core switches...')
        for x in self.CoreSwitches:
            print(f'ID: {x.id} TYPE: {x.type}')

        print('\nPrinting aggregation switches...')
        for x in self.AggSwitches:
            print(f'ID: {x.id} TYPE: {x.type}')

        print('\nPrinting edge switches...')
        for x in self.EdgeSwitches:
            print(f'ID: {x.id} TYPE: {x.type}')

        print('\nPrinting generated servers...')
        for x in self.Servers:
            print(f'ID: {x.id} TYPE: {x.type}')

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


# Building Fattree with 8 switch ports
if __name__ == '__main__':
    tree = Fattree(8)
    all_nodes = tree.CoreSwitches + tree.AggSwitches + tree.EdgeSwitches + tree.Servers
    draw_topology(all_nodes)


