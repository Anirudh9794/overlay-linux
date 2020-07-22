from overlay_north.python_models import subnet_model
from overlay_north.python_models import vpc_model
from overlay_north.python_models import transit_model
from overlay_north.python_models import tunnel_model
from overlay_north.provider_db import ProviderDb
import json
import subprocess
import ipaddress
import traceback
from typing import List


class TunnelHandler:
    def __init__(self):
        self.db = ProviderDb()
        self.SOUTHBOUND_DIRECTORY = 'overlay_south'

    def create_tunnel(self, args):
        customer_id = args["customerId"]
        vpc_id = args["vpcId"]
        tunnel_type = str(args["tunnelType"]).lower()  # "l2" or "l3"

        if tunnel_type != "l3" and tunnel_type != "l2":
            return {"message": "Invalid tunnelType. Either 'l2' or 'l3'. Fix this --> {0}".format(tunnel_type), "success": False}

        # verify customer id
        if (self.db.get_customer_by_id(customer_id) == None):
            return {"message": "No customer found with id '{0}'".format(customer_id), "success": False}

        # verify vpc id
        vpc = self.db.get_vpc_by_id(vpc_id, customer_id)
        if(vpc == None):
            return {"message": "No vpc found with id '{0}' for customer '{1}'".format(vpc_id, customer_id), "success": False}

        # verify transit id
        transit = self.db.get_transit(customer_id)
        if(transit == None):
            return {"message": "No transit found for customer '{0}'".format(customer_id), "success": False}

        # get db id for transit router
        tunnel_id = self.db.get_next_tunnel_id()
        if tunnel_id < 0:
            return {"message": "A SQL error occured in creating ({0}) tunnel between transit and vpc (id = {1})".format(tunnel_type, vpc_id), "success": False}
        if tunnel_type == 'l3':
            if self.create_physically_l3(vpc, transit, customer_id):
                # save in db if successful
                return self.create_in_db(transit.transit_id, vpc_id, tunnel_type)
            else:
                return {"message": "Unable to physically create the ({0}) tunnel between transit and vpc (id = {1})".format(tunnel_type, vpc_id), "success": False}
        elif tunnel_type == 'l2':
            if self.create_physically_l2(vpc, transit, customer_id):
                # save in db if successful
                return self.create_in_db(transit.transit_id, vpc_id, tunnel_type)
            else:
                return {"message": "Unable to physically create the ({0}) tunnel between transit and vpc (id = {1})".format(tunnel_type, vpc_id), "success": False}

    def create_physically_l2(self, vpc, transit, customer_id):
        print("Inside tunnel_handler.create_physically")
        result = False
        vpc_host = vpc.host.lower()
        transit_host = transit.host.lower()

        # transit = self.db.get_next_transit_id()
        # if subnet_id < 0:
        #     return {"message": "A SQL error occured in creating subnet '{0}'".format(ip_address), "success": False}

        try:
            json_obj = {}
            json_obj['vpc_id'] = vpc.vpcId
            json_obj['scalability_factor'] = vpc.scaleFactor
            json_obj["reliability_factor"] = transit.reliability_factor
            json_obj["transit_id"] = transit.transit_id

            vars_json = json.dumps(json_obj)
            commands = [
                "sudo",
                "ansible-playbook",
                "-i",
                "hosts.ini",
                "create-vxlan-at-edge.yml",
                "-l {0}".format(vpc_host),
                "-e",
                vars_json
            ]
            p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
            p.wait()

            if p.returncode != 0:
                print(
                    "\r\nUnable to run ansible 'create-vxlan-at-edge.yml' for transit '{0}' for customer '{1}'\r\n".format(transit.transit_id, customer_id))
                return False
            
            commands = [
                "sudo",
                "ansible-playbook",
                "-i",
                "hosts.ini",
                "create-vxlan-at-transit.yml",
                "-l {0}".format(transit_host),
                "-e",
                vars_json
            ]
            p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
            p.wait()

            if p.returncode != 0:
                print(
                    "\r\nUnable to run ansible 'create-vxlan-at-transit.yml' for transit '{0}' and vpc '{1}'\r\n".format(transit.transit_id, vpc.vpcId))
                return False

            result = True
        except Exception as e:
            print(
                "\r\nUnable to physically create the tunnel for transit '{0}' and vpc '{1}'\r\nException below:\r\n{2}".format(transit.transit_id, vpc.vpcId, e))
            result = False

        return result

    def create_physically_l3(self, vpc, transit, customer_id):
        print("Inside tunnel_handler.create_physically")
        result = False
        vpc_host = vpc.host.lower()
        transit_host = transit.host.lower()

        # transit = self.db.get_next_transit_id()
        # if subnet_id < 0:
        #     return {"message": "A SQL error occured in creating subnet '{0}'".format(ip_address), "success": False}

        try:
            json_obj = {}
            json_obj['vpc_id'] = vpc.vpcId
            json_obj['scalability_factor'] = vpc.scaleFactor
            json_obj["reliability_factor"] = transit.reliability_factor
            json_obj["transit_id"] = transit.transit_id

            vars_json = json.dumps(json_obj)
            commands = [
                "sudo",
                "ansible-playbook",
                "-i",
                "hosts.ini",
                "create-gre-at-edge.yml",
                "-l {0}".format(vpc_host),
                "-e",
                vars_json
            ]
            p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
            p.wait()

            if p.returncode != 0:
                print(
                    "\r\nUnable to run ansible 'create-gre-at-edge.yml' for transit '{0}' for customer '{1}'\r\n".format(transit.transit_id, customer_id))
                return False
            
            commands = [
                "sudo",
                "ansible-playbook",
                "-i",
                "hosts.ini",
                "create-gre-at-transit.yml",
                "-l {0}".format(transit_host),
                "-e",
                vars_json
            ]
            p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
            p.wait()

            if p.returncode != 0:
                print(
                    "\r\nUnable to run ansible 'create-gre-at-transit.yml' for transit '{0}' and vpc '{1}'\r\n".format(transit.transit_id, vpc.vpcId))
                return False

            result = True
        except Exception as e:
            print(
                "\r\nUnable to physically create the tunnel for transit '{0}' and vpc '{1}'\r\nException below:\r\n{2}".format(transit.transit_id, vpc.vpcId, e))
            result = False

        return result

        # return True  # TODO: Fix this!

    def create_in_db(self, transit_id, vpc_id, tunnel_type):

        tunnel_id = self.db.create_tunnel(
            transit_id, vpc_id, tunnel_type)

        if tunnel_id < 0:
            return {"message": "failed to create ({0}) tunnel between transit (id={1}) and vpc (id={2}). Tunnel id is '{3}'".format(
                tunnel_type, transit_id, vpc_id, tunnel_id), "success": False}
        else:
            return {"message": "Created ({0}) tunnel between transit (id={1}) and vpc (id={2}). Tunnel id is '{3}'".format(
                tunnel_type, transit_id, vpc_id, tunnel_id), "success": True}

    def delete_tunnel(self, args):
        customer_id = args["customerId"]
        tunnel_id = args["tunnelId"]

        # verify customer id
        if (self.db.get_customer_by_id(customer_id) == None):
            return {"message": "No customer found with id '{0}'".format(customer_id), "success": False}

        tunnel = self.db.get_tunnel(tunnel_id)
        if tunnel == None:
            return {"message": "No tunnel found with id '{0}'".format(tunnel_id), "success": False}

        else:
            if self.delete_physically_l3():
                if self.db.delete_tunnel(tunnel_id):
                    return {"message": "Successfully deleted Tunnel with id '{0}' ".format(tunnel_id), "success": True}
                else:
                    return {"message": "Failed to delete from db Tunnel with id '{0}' ".format(tunnel_id), "success": False}
            else:
                return {"message": "Failed to physically delete Tunnel with id '{0}' ".format(tunnel_id), "success": False}

    def delete_physically_l3(self):
        print("Inside tunnel_handler.delete_physically")
        return True  # TODO: Fix this!

