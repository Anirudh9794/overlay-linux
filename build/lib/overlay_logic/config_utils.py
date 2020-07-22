import os

class Network(object):
    def __init__(self, address):
        self.ip_address = address

    def get_string(self):
        network_string=""
        network_string = network_string + "network {1}\n".format(self.ip_address)
        return network_string

class Neighbor(object):
        def __init__(self, neighbor_ip, remote_as, disable_connected_check, hops):
            self.neighbor_ip = neighbor_ip
            self.remote_as = remote_as
            self.disable_connected_check = disable_connected_check
            self.hops = hops
        
        def get_string(self):
            neighbor_string = ""
            neighbor_string =  neighbor_string + "neighbor {1} remote-as {2} \n".\
                format(self.neighbor_ip, self.remote_as)
            if self.disable_connected_check:
                neighbor_string = neighbor_string + "neighbor {1} disable-connected-check".\
                    format(self.neighbor_ip)
            if self.hops:
                neighbor_string = neighbor_string + "neighbor {1} ttl-security hops {2}".\
                    format(self.neighbor_ip, self.hops)
            return neighbor_string

class AS(object):
    def __init__(self, asn):
        self.asn = asn
        self.router_ids = []
        self.networks = []
        self.neighbors = []
        
    def add_network(self, address):
        net = Network(address)
        self.networks.append(net)

    def add_router_id(self, addr):
        self.router_ids.append(addr)
    
    def add_neighbor(self, neighbor_ip, remote_as, disable_connected_check, hops):
        neigh = Neighbor(neighbor_ip,remote_as, disable_connected_check, hops)
        self.neighbors.append(neigh)

class config_utils:
    def __init__ (self) :
        self.BGP_CONFIG_DIRECTORY = os.path.dirname(os.path.realpath(__file__)).\
                    replace("overlay_north", "overlay_south") + "/bgp/"

        self.autonomus_systems = []
    
    def add_as(self, as_obj):
        self.autonomus_systems.append(as_obj)

    def write_config_to(self, filename):
        config = ""
        for a in self.autonomus_systems:
            config = config + "hostname bgpd" + "\n"
            config = config + "password zebra" + "\n"
            config = config + "log file /var/log/quagga/bgpd.log" + "\n"
            config = config + "debug bgp updates" + "\n"

            config = config + "router bgp " + str(a.asn)

            for router_id in a.router_ids:
                config = config + "bgp router-id " + router_id + "\n"

            config = config + "\nredistribute kernel\nredistribute connected\n"

            for n in a.networks:
                config = config + n.get_string() + "\n"

            for n in a.neighbors:
                config = config + n.get_string() + "\n"

            config = "end\n"

        with open(self.BGP_CONFIG_DIRECTORY, filename, "w") as fd:
            fd.write(config)
            fd.close()