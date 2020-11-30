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

# !/usr/bin/env python3
import collections

from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase

import topo
import copy


class SPRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SPRouter, self).__init__(*args, **kwargs)
        self.topo_raw_switches = []
        self.topo_raw_links = []
        self.switches = []
        self.switches_links = []
        self.datapath_list = []
        self.mac_to_port = {}
        self.fat_tree_topo = topo.Fattree(4)
        self.ip_to_id, self.id_to_ip = self.create_mappings()
        self.shortest_paths_for_all_nodes = self.calculate_all_shortest_path_routs_for_servers()

        self.adjacency = collections.defaultdict(lambda: collections.defaultdict(lambda: None))

    def create_mappings(self):
        all_nodes = self.fat_tree_topo.servers + self.fat_tree_topo.edge_switches + self.fat_tree_topo.agg_switches + \
            self.fat_tree_topo.core_switches
        ip_to_id = {node.ip_address: node.id for node in all_nodes}
        id_to_ip = {node.id: node.ip_address for node in all_nodes}

        return ip_to_id, id_to_ip

    def calculate_all_shortest_path_routs_for_servers(self):
        all_nodes = self.fat_tree_topo.servers + self.fat_tree_topo.core_switches + self.fat_tree_topo.agg_switches + \
                    self.fat_tree_topo.edge_switches

        all_paths = {}
        for server in self.fat_tree_topo.servers:
            all_paths[server.ip_address] = self.get_shortest_paths(server, all_nodes)

        return all_paths

    def get_shortest_paths(self, server, all_nodes):
        distance = {}
        previous = {}

        for node in all_nodes:
            distance[node.ip_address] = float('inf')
            previous[node.ip_address] = None

        distance[server.ip_address] = 0

        visited_set = set(all_nodes)
        while len(visited_set) > 0:
            node_with_smallest_distance = self.minimum_distance(distance, visited_set)
            visited_set.remove(node_with_smallest_distance)

            for node in all_nodes:
                if node_with_smallest_distance.is_neighbor(node):
                    weight = 1
                    if distance[node_with_smallest_distance.ip_address] + weight < \
                            distance[node.ip_address]:
                        distance[node.ip_address] = distance[node_with_smallest_distance.ip_address] + weight
                        previous[node.ip_address] = node_with_smallest_distance.ip_address

        return previous

    def minimum_distance(self, distance, visited_set):
        min = float('Inf')
        selected = list(visited_set)[0]

        for node in visited_set:
            if distance[node.ip_address] < min:
                min = distance[node.ip_address]
                selected = node

        return selected

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):

        # Switches and links in the network

        switch_list = copy.copy(get_switch(self, None))

        self.switches = [switch.dp.id for switch in switch_list]
        self.datapath_list = [switch.dp for switch in switch_list]

        print(f"switches={self.switches}")

        self.switches_links = copy.copy(get_link(self, None))

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install entry-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    # Add a flow entry to the flow-table
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Construct flow_mod message and send it
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        switch_ip = self.id_to_ip['sw'+str(dpid)]

        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            self.mac_to_port[dpid][src] = in_port
            arp_pkt = pkt.get_protocol(arp.arp)
            dst_ip = arp_pkt.dst_ip
            type_of_eth = 'ARP'
        elif eth.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            dst_ip = ip_pkt.dst
            type_of_eth = 'IP'
        else:
            return

        print(f'[{dpid}][{in_port}][{type_of_eth}]{src}][{dst}][Destination Ip: {dst_ip}]')

        next_ip = self.shortest_paths_for_all_nodes[dst_ip][switch_ip]
        next_dpid = self.ip_to_id[next_ip]

        if next_ip == dst_ip:
            if dst in self.mac_to_port[dpid]:
                out_port = self.mac_to_port[dpid][dst]
            else:
                out_port = ofproto.OFPP_FLOOD
        else:
            out_port = list(filter(lambda l:
                                   l.src.dpid == dpid and
                                   'sw' + str(l.dst.dpid) == next_dpid,
                                   self.switches_links))[0].src.port_no

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD and eth.ethertype == ether_types.ETH_TYPE_IP:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            print(f'Adding flow: switch: {dpid} in_port: {in_port}, out_port: {out_port}, src: {src}, dst: {dst}')
            self.add_flow(datapath, 1, match, actions)

        out = parser.OFPPacketOut(datapath=datapath, in_port=in_port, actions=actions,
                                  buffer_id=datapath.ofproto.OFP_NO_BUFFER, data=msg.data)

        datapath.send_msg(out)

