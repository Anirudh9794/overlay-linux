from overlay_north.python_models import subnet_model
from overlay_north.python_models import vpc_model
from overlay_north.python_models import transit_model
from overlay_north.provider_db import ProviderDb
import json
import subprocess
import ipaddress
import traceback
from typing import List
import overlay_logic.config_utils as cfg


class TransitHandler:
    def __init__(self):
        self.db = ProviderDb()
        self.SOUTHBOUND_DIRECTORY = 'overlay_south'
        self.bgp_config = []

    def create_transit(self, args):
        #
        customer_id = args["customerId"]
        host = args["host"]
        reliability_factor = int(
            args["reliabilityFactor"])  # must be an integer!

        # verify customer id
        if (self.db.get_customer_by_id(customer_id) == None):
            return {"message": "No customer found with id '{0}'".format(customer_id), "success": False}

        # Only 1 transit per customer
        transit = self.db.get_transit(customer_id)
        if transit != None:
            return {"message": "A transit (id = {0}) already exists for customer '{1}'!".format(transit.transit_id, customer_id), "success": False}

        # get db id for transit
        transit_id = self.db.get_next_transit_id()
        if transit_id < 0:
            return {"message": "A SQL error occured in creating the transit", "success": False}
        # create bgp config 
        for i in range(int(reliability_factor)):
            config_obj = cfg.config_utils()
            asnum = "1%s%s" % (transit_id, i)
            config_as = cfg.AS(asnum)
            config_obj.add_as(config_as)
            self.bgp_config.append(config_obj)
            filename = "edge-%s-%s.conf" % (transit_id, i)
            config_obj.write_config_to(filename)

        if self.create_physically(transit_id, customer_id, host, reliability_factor):
            # save in db if successful
            return self.create_in_db(customer_id, host, reliability_factor)
        else:
            return {"message": "Unable to physically create the transit routers", "success": False}

    def create_physically(self, transit_id, customer_id, host, reliability_factor):
        print("Inside transit_handler.create_physically")
        # call the playbook create-transit.yml
        result = False
        host = host.lower()

        transit = self.db.get_next_transit_id()
        # if subnet_id < 0:
        #     return {"message": "A SQL error occured in creating subnet '{0}'".format(ip_address), "success": False}

        try:
            json_obj = {}
            json_obj["reliability_factor"] = reliability_factor
            json_obj["transit_id"] = transit_id

            vars_json = json.dumps(json_obj)
            commands = [
                "sudo",
                "ansible-playbook",
                "-i",
                "hosts.ini",
                "create-transit.yml",
                "-l {0}".format(host),
                "-e",
                vars_json
            ]
            p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
            p.wait()

            if p.returncode != 0:
                print(
                    "\r\nUnable to run ansible 'create-transit.yml' for transit '{0}' for customer '{1}'\r\n".format(transit_id, customer_id))
                return False

            # add routes to remote
            for i in range(reliability_factor):
                json_obj = {}
                json_obj["router_number"] = i
                json_obj['transit_id'] = transit_id
                vars_json = json.dumps(json_obj)
                other_host = 'host1'
                if host == 'host1':
                    other_host = 'host2'
                commands = [
                    "sudo",
                    "ansible-playbook",
                    "-i",
                    "hosts.ini",
                    "transit-route-to-host.yml",
                    "-l {0}".format(other_host),
                    "-e",
                    vars_json
                ]
                p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
                p.wait()
                if p.returncode != 0:
                    print(
                        "\r\nUnable to run ansible 'create-transit.yml' for transit '{0}' for customer '{1}'\r\n".format(transit_id, customer_id))
                    return False
            result = True
        except Exception as e:
            print(
                "\r\nUnable to physically create the transit '{0}' for customer id '{1}'\r\nException below:\r\n{2}".format(transit_id, customer_id, e))
            result = False

        return result

    def create_in_db(self, customer_id, host, reliability_factor) -> list:
        transitId = self.db.create_transit(
            customer_id, host, reliability_factor)

        if int(transitId) < 0:
            return {"message": "failed to create transit for customer '{0}'".format(
                customer_id), "success": False}
        else:
            return {"message": "Created transit '{0}' for customer '{1}'. Can call '.../tunnel' to add VPCs to this transit.".format(
                transitId, customer_id), "success": True}

    def get_transit(self, args):
        customer_id = args["customerId"]

        # verify customer id
        if (self.db.get_customer_by_id(customer_id) == None):
            return {"message": "No customer found with id '{0}'".format(customer_id), "success": False}

        transit = self.db.get_transit(customer_id)
        if transit == None:
            return {"message": "No transit found for customer {0}".format(customer_id), "success": False}
        else:
            # have to format Tunnel class into dict here...
            tunnels = []
            for tun in transit.tunnels:
                tunnels.append(
                    {"tunnelId": tun.tunnel_id, "vpcId": tun.vpc_id, "tunnelType": tun.tunnel_type})

            return {
                "message": {
                    "transitId": transit.transit_id,
                    "host": transit.host,
                    "reliabiltyFactor": transit.reliability_factor,
                    "tunnels": tunnels
                },
                "success": True
            }

    def delete_transit(self, args):
        customer_id = args["customerId"]

        # verify customer id
        if (self.db.get_customer_by_id(customer_id) == None):
            return {"message": "No customer found with id '{0}'".format(customer_id,), "success": False}

        res = self.db.get_transit(customer_id)
        if not res:
            return {"message": "No transit found for the customer {1}".format(customer_id,), "success": False}
        tunnels = res.tunnels

        if len(tunnels) != 0:
            tunnels_id_list = []
            for tunnel in tunnels:
                tunnels_id_list.append(tunnel.tunnel_id)
            return {"message": "For customer '{0}'...Please delete these tunnels (id shown)".format(customer_id), "tunnelIdList": tunnels_id_list, "success": False}
        else:
            ok = self.delete_physically(res.transit_id, customer_id, res.host, res.reliability_factor)
            if ok and self.db.delete_transit(customer_id):
                return {"message": "For customer '{0}'...successfully deleted your transit.".format(customer_id), "success": True}
            else:
                return {"message": "For customer '{0}'...failed to delete your transit.".format(customer_id), "success": False}

    def delete_physically(self, transit_id, customer_id, host, reliability_factor):
        print("Inside transit_handler.create_physically")
        result = False
        host = host.lower()
        
        try:
            json_obj = {}
            json_obj["reliability_factor"] = reliability_factor
            json_obj["transit_id"] = transit_id

            vars_json = json.dumps(json_obj)
            commands = [
                "sudo",
                "ansible-playbook",
                "-i",
                "hosts.ini",
                "delete-transit.yml",
                "-l {0}".format(host),
                "-e",
                vars_json
            ]
            p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
            p.wait()

            if p.returncode != 0:
                print(
                    "\r\nUnable to run ansible 'delete-transit.yml' for transit '{0}' for customer '{1}'\r\n".format(transit_id, customer_id))
                return False
            
            #####TODO creation vars in transit route add also
            for i in range(reliability_factor):
                json_obj = {}
                json_obj["creation_vars"] = [{
                    "router_number": i,
                    "transit_id": transit_id
                }]
                vars_json = json.dumps(json_obj)
                other_host = 'host1'
                if host == 'host1':
                    other_host = 'host2'

                commands = [
                    "sudo",
                    "ansible-playbook",
                    "-i",
                    "hosts.ini",
                    "delete-transit-route-to-host.yml",
                    "-l {0}".format(other_host),
                    "-e",
                    vars_json
                ]

                p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
                p.wait()

            result = True
        except Exception as e:
            print(
                "\r\nUnable to physically delete the transit '{0}' for customer id '{1}'\r\nException below:\r\n{2}".format(transit_id, customer_id, e))
            result = False

        return result
