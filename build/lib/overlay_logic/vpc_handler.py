from overlay_north.python_models import vpc_model
from overlay_north.provider_db import ProviderDb
import json
import subprocess
import os
from .config_utils import *

class VPCHandler():
    def __init__(self):
        self.db = ProviderDb()
        self.SOUTHBOUND_DIRECTORY = 'overlay_south'
        
        self.bgpConfig = []

    def get_vpc_by_hosts(self, args):
        customerId = args["customerId"]
        print(args)
        print("\r\nThe customer Id is: {0}\r\n".format(customerId))
        output = {}
        vpc_list = self.db.get_all_vpcs(customerId)
        print("\r\n THe vpc_list is: {0}\r\n".format(vpc_list))
        output["message"] = "The list of VPC IDs are: '{0}'".format(vpc_list)
        output["success"] = True
        return output

    def create_vpc(self, args):
        vpcName = args["vpcName"]
        customerId = args["customerId"]
        host = args["host"]
        scaleFactor = args["scaleFactor"]

        if(self.db.get_customer_by_id(customerId) == None):
            return {"message": "No customer found with id '{0}'".format(customerId), "success": False}

        if(self.db.get_vpc(vpcName, customerId, host) != None):
            return {"message": "vpc '{0}' already exists for host '{1}'".format(vpcName, host), "success": False}

        vpc_id = self.db.get_next_vpc_id()
        if vpc_id < 0:
            return {"message": "A SQL error occured in creating vpc '{0}'".format(vpcName), "success": False}

        self.bgp_config = [cfg.config_utils()] * scaleFactor
        for i in range(scaleFactor):
            config_obj = cfg.config_utils()
            config_as = cfg.AS(int("1{1}{2}".format(vpc_id, i)))
            config_obj.add_as(config_as)
            self.bgp_config.append(config_obj)
            config_obj.write_config_to("edge-{1}-{2}.conf".format(vpc_id, i))

        if self.create_physically(vpc_id, host, scaleFactor):
            # save in db if successful
            db_result = self.create_in_db(
                vpcName, customerId, host, scaleFactor)
            return db_result

        # TODO: Remove this below!
        # db_result = self.create_in_db(
        #     vpcName, customerId, host, scaleFactor)
        # return db_result

        return {"message": "failed to create vpc {0}".format(vpcName), "success": False}

    def create_in_db(self, vpcName, customerId, host, scaleFactor):
        # create vpc in db
        vpcId_str = self.db.create_vpc(vpcName, customerId, host, scaleFactor)
        if(vpcId_str != None):
            return {"message": "vpc created. Id is '{0}'".format(vpcId_str), "success": True}
        else:
            return {"message": "failed to create vpc '{0}'".format(vpcName), "success": False}

    def delete_vpc(self, args):
        vpc_id = args["vpcId"]
        customer_id = args["customerId"]

        # ensure customer is valid
        if(self.db.get_customer_by_id(customer_id) == None):
            return {
                "message": "No customer found with id '{0}'".format(customer_id),
                "success": False
            }

        # get vpc id
        vpc = self.db.get_vpc_by_id(vpc_id, customer_id)
        if (vpc == None):
            return {
                "message": "No vpc found with id '{0}' for customer '{1}'".format(vpc_id, customer_id),
                "success": False
            }

        # get a list of subnets
        subnet_ip_list = self.db.get_all_subnets_ip(vpc_id)

        if len(subnet_ip_list) > 0:
            return {
                "message": "Please delete these subnets from vpc '{0}'".format(vpc_id),
                "ipList": subnet_ip_list,
                "success": False
            }
        else:
            # delete vpc
            vpc_del_ok = self.delete_physically(
                vpc.vpcId, vpc.scaleFactor, vpc.host) and self.db.delete_vpc(vpc.vpcId)

            if not vpc_del_ok:
                return {
                    "message": "Failed to delete vpc '{0}'. Does it exist?".format(vpc_id),
                    "success": False
                }
            else:
                return {
                    "message": "Successfully deleted vpc '{0}'.".format(vpc_id),
                    "success": True
                }
    # might have to change the names of the south -bound scripts

    def create_physically(self, vpc_id, host, scale_factor):
        scale_factor = int(scale_factor)
        for i in range(scale_factor):
            json_obj = {}
            json_obj["creation_vars"] = [{"vpc_id": vpc_id, "edge_number": i}]
            vars_json = json.dumps(json_obj)
            commands = [
                "sudo",
                "ansible-playbook",
                "create-edges.yml",
                "-i",
                "hosts.ini",
                "-e",
                vars_json,
                "-l {0}".format(host.lower())
            ]
            p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
            p.wait()

            if p.returncode != 0:
                print(
                    "\r\nUnable to run ansible 'create-edges.yml' in vpc_handler.create_physically\r\n")
                return False

            other_host = 'host2' if host == 'Host1' else 'host1'

            commands = [
                "sudo",
                "ansible-playbook",
                "edge-route-to-host.yml",
                "-i",
                "hosts.ini",
                "-e",
                vars_json,
                "-l {0}".format(other_host)
            ]
            p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
            p.wait()

            if p.returncode != 0:
                print(
                    "\r\nUnable to run ansible 'edge-route-to-host.yml' in vpc_handler.create_physically\r\n")
                return False

        return True

    def delete_physically(self, vpc_id, scaleFactor, host):
        for i in range(scaleFactor):
            json_obj = {}
            json_obj["creation_vars"] = [{"vpc_id": vpc_id, "edge_number": i}]
            vars_json = json.dumps(json_obj)
            commands = [
                "sudo",
                "ansible-playbook",
                "delete-edges.yml",
                "-i",
                "hosts.ini",
                "-e",
                vars_json,
                "-l {0}".format(host.lower())
            ]
            p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
            p.wait()

            if p.returncode != 0:
                print(
                    "\r\nUnable to run ansible 'delete-edges.yml' in vpc_handler.delete_physically\r\n")
                return False

            other_host = 'host2' if host == 'Host1' else 'host1'

            commands = [
                "sudo",
                "ansible-playbook",
                "delete-routes-to-edges.yml",
                "-i",
                "hosts.ini",
                "-e",
                vars_json,
                "-l {0}".format(other_host)
            ]
            p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
            p.wait()

            if p.returncode != 0:
                print(
                    "\r\nUnable to run ansible 'delete-routes-to-edges.yml' in vpc_handler.delete_physically\r\n")
                return False

        return True
