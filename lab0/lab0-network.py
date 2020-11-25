from mininet.topo import Topo


class Lab0Topo(Topo):
    def __init__(self):
        Topo.__init__(self)

        link_opts = dict(bw=15, delay='10ms')
        link_opts_switches = dict(bw=20, delay='45ms')

        host1=self.addHost('h1', ip='10.0.0.1/8')
        host2=self.addHost('h2', ip='10.0.0.2/8')
        switch1=self.addSwitch('s1')

        host3=self.addHost('h3', ip='10.0.0.3/8')
        host4=self.addHost('h4', ip='10.0.0.4/8')
        switch2=self.addSwitch('s2')

        self.addLink(host1, switch1, **link_opts)
        self.addLink(host2, switch1, **link_opts)

        self.addLink(host3, switch2, **link_opts)
        self.addLink(host4, switch2, **link_opts)

        self.addLink(switch1, switch2, **link_opts_switches)


topos = { 'lab0topo': (lambda: Lab0Topo()) }