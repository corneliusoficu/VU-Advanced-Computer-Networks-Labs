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
import pprint
import ctypes
import ipaddress
import re

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
import socket,struct


class FTRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        self.switches = []
        self.links = []
        super(FTRouter, self).__init__(*args, **kwargs)
        self.topo_net = topo.Fattree(4)
        self.ip_to_id, self.id_to_ip = self.create_mappings()
        self.core_switches_routing_table = {}
        self.routing_table_prefixes = {}
        self.routing_table_suffixes = {}
        self.create_2_way_routing_table()
        self.mac_to_port = {}

    def network_mask(self, network_str):
        n = ipaddress.ip_network(network_str, strict=False)
        netw = int(n.network_address)
        mask = int(n.netmask)
        return network_str, netw, mask

    def is_address_in_network(self, ip, netw, mask):
        a = int(ipaddress.ip_address(ip))
        return (a & mask) == netw

    def create_mappings(self):
        all_nodes = self.topo_net.servers + self.topo_net.edge_switches + self.topo_net.agg_switches + \
                    self.topo_net.core_switches
        ip_to_id = {node.ip_address: node.id for node in all_nodes}
        id_to_ip = {node.id: node.ip_address for node in all_nodes}

        return ip_to_id, id_to_ip

    def extract_ip(self, ip_str):
        l = re.split(r'(.*)\.(.*)\.(.*)\.(.*)', ip_str)
        return l[1:-1]

    def create_2_way_routing_table(self):
        for pod in range(0, self.topo_net.num_pods):
            for switch in range(int(self.topo_net.num_ports / 2), self.topo_net.num_ports):
                for subnet in range(0, int(self.topo_net.num_ports / 2)):
                    switch_ip_address = f'10.{pod}.{switch}.1'
                    switch_prefix = f'10.{pod}.{subnet}.0/24'
                    next_hop = f'10.{pod}.{subnet}.1'
                    self.routing_table_prefixes.setdefault(switch_ip_address, []).append((switch_prefix, next_hop, 2))
                for id in range(2, int(self.topo_net.num_ports / 2) + 2):
                    switch_ip_address = f'10.{pod}.{switch}.1'
                    switch_suffix = f'0.0.0.{id}'
                    port = int(((id - 2 + switch) % (self.topo_net.num_ports / 2)) + (self.topo_net.num_ports / 2))
                    next_hop = f'10.{self.topo_net.num_pods}.{switch - (int(self.topo_net.num_ports / 2) - 1)}.{port - 1}'
                    self.routing_table_suffixes.setdefault(switch_ip_address, []).append((switch_suffix, next_hop, 1))

        for j in range(1, int(self.topo_net.num_ports / 2) + 1):
            for i in range(1, int(self.topo_net.num_ports / 2) + 1):
                for x in range(0, self.topo_net.num_ports):
                    switch_ip_address = f'10.{self.topo_net.num_ports}.{j}.{i}'
                    switch_prefix = f'10.{x}.0.0/16'
                    next_hop = f'10.{x}.{j + (int(self.topo_net.num_ports / 2) - 1)}.1'
                    self.routing_table_prefixes.setdefault(switch_ip_address, []).append((switch_prefix, next_hop, 1))

        for pod in range(0, self.topo_net.num_pods):
            for i in range(0, int(self.topo_net.num_ports / 2)):
                switch_ip_address = f'10.{pod}.{i}.1'
                for host_id in range(2, int(self.topo_net.num_ports/2) + 2):
                    switch_prefix = f'10.{pod}.{i}.{host_id}/32'
                    self.routing_table_prefixes.setdefault(switch_ip_address, []).append((switch_prefix,
                                                                                 f'10.{pod}.{i}.{host_id}', 1))

                switch_prefix = f'0.0.0.0/0'
                next_hop = f'10.{pod}.{i + int(self.topo_net.num_ports / 2)}.1'
                self.routing_table_prefixes.setdefault(switch_ip_address, []).append((switch_prefix, next_hop, 1))

        self.routing_table_prefixes = {
            self.ip_to_id[key]: [(self.network_mask(value2[0]), self.ip_to_id[value2[1]], value2[1], value2[2]) for value2 in value]
           for key, value in self.routing_table_prefixes.items()}

        self.routing_table_suffixes = {
            self.ip_to_id[key]: [(value2[0], self.ip_to_id[value2[1]], value2[1], value2[2]) for value2 in value]
            for key, value in self.routing_table_suffixes.items()}

        print("Routing table prefixes: ")
        pprint.pprint(self.routing_table_prefixes)
        print("Routing table suffixes: ")
        pprint.pprint(self.routing_table_suffixes)

    def get_next_hop_for_current_switch(self, current_sw, destination_ip):
        routing_information_list = self.routing_table_prefixes[current_sw]

        for routing_information in routing_information_list:
            network_str, netw, mask = routing_information[0]
            hop = routing_information[1]
            hop_ip_address = routing_information[2]
            priority = routing_information[3]
            if self.is_address_in_network(destination_ip, netw, mask):
                return hop, hop_ip_address, priority

        routing_information_list = self.routing_table_suffixes[current_sw]

        for routing_information in routing_information_list:
            ip_addr, hop, hop_ip_address, priority = routing_information
            if self.extract_ip(destination_ip)[3] == self.extract_ip(ip_addr)[3]:
                return hop, hop_ip_address, priority

        raise Exception(f"No route could be identified for ip: {destination_ip}, switch: {current_sw}")

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        # Switches and links in the network
        switches = get_switch(self, None)
        self.switches = [switch.dp.id for switch in switches]

        self.switches_links = get_link(self, None)
        print(f"{len(self.switches)} Switches={self.switches}")
        print(f"{len(self.switches_links)} links")

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
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

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

        next_dpid, next_ip_addr, priority = self.get_next_hop_for_current_switch(f'sw{dpid}', dst_ip)

        print(f"sw{dpid} -> {next_dpid}, {next_ip_addr}")

        if next_ip_addr == dst_ip:
            if dst in self.mac_to_port[dpid]:
                out_port = self.mac_to_port[dpid][dst]
            else:
                out_port = ofproto.OFPP_FLOOD
        else:
            for link in self.switches_links:
                if link.src.dpid == dpid and 'sw' + str(link.dst.dpid) == next_dpid:
                    out_port = link.src.port_no
                    break
                elif link.dst.dpid == dpid and 'sw'+str(link.src.dpid) == next_dpid:
                    out_port = link.dst.port_no
                    break

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD and eth.ethertype == ether_types.ETH_TYPE_IP:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            print(f'Adding flow: switch: {dpid} in_port: {in_port}, out_port: {out_port}, src: {src}, dst: {dst}')
            self.add_flow(datapath, priority, match, actions)

        out = parser.OFPPacketOut(datapath=datapath, in_port=in_port, actions=actions,
                                  buffer_id=datapath.ofproto.OFP_NO_BUFFER, data=msg.data)

        datapath.send_msg(out)
