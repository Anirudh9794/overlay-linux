from overlay_north.python_models import subnet_model
from overlay_north.python_models import vpc_model
from overlay_north.provider_db import ProviderDb
import json
import subprocess
import ipaddress
import traceback


class SubnetHandler:

    def __init__(self):
        self.db = ProviderDb()
        self.SOUTHBOUND_DIRECTORY = 'overlay_south'

    def get_all_subnets(self, args) -> list:
        customer_id = args["customerId"]

        vpc_id_list = self.db.get_all_vpcs(customer_id)
        ret_list = []

        for vpc_id in vpc_id_list:
            vpc = self.db.get_vpc_by_id(vpc_id, customer_id)
            subnets = self.db.get_all_subnets(vpc_id)
            sub_list = []

            for subnet in subnets:
                s = {}
                s["subnetId"] = subnet.subnetId
                s["vpcId"] = subnet.vpcId
                s["ipAddress"] = subnet.ipAddress
                s["subnetName"] = subnet.subnetName

                sub_list.append(s)

            ret_list.append(
                {"vpcId": vpc_id, "vpcName": vpc.vpcName, "host": vpc.host, "subnets": sub_list})

        return {"message": ret_list, "success": True}

    def create_subnet(self, args):
        customer_id = args["customerId"]
        vpc_id = args["vpcId"]
        subnet_str = args["subnet"]

        if (self.db.get_customer_by_id(customer_id) == None):
            return {"message": "No customer found with id '{0}'".format(customer_id), "success": False}

        # get vpc
        vpc = self.db.get_vpc_by_id(vpc_id, customer_id)
        if(vpc == None):
            return {"message": "No vpc found with id '{0}' for customer '{1}'".format(vpc_id, customer_id), "success": False}

        # convert str to dict
        subnet_str = subnet_str.replace("\'", "\"")
        subnet = json.loads(subnet_str)
        ip_address = subnet["ipAddress"]
        subnet_name = subnet["subnetName"]

        # verify valid ip NETWORK address
        ip_ok, ip_error = self.ensure_valid_ip_network(ip_address)
        if not ip_ok and ip_error == None:
            return {"message": "Invalid ip given! Fix this --> '{0}' ".format(ip_address), "success": False}
        if not ip_ok and ip_error != None:
            return {"message": "Invalid ip NETWORK address given! The network address is: '{0}'! Fix this --> '{1}' ".format(ip_error, ip_address), "success": False}

        # check db to see if subnet exists
        if(self.db.get_subnet(ip_address, vpc_id) != None):
            return {
                "message": "subnet '{0}' for vpc {1} (id '{2}') already exists".format(
                    ip_address, vpc.vpcName, vpc_id),
                "success": False
            }
        else:
            # save in db if successful
            if self.create_physically(ip_address, vpc_id, vpc.host, vpc.scaleFactor):
                subnetId = self.create_in_db(vpc_id, ip_address, subnet_name)
                return {
                    "subnet_id":subnetId,
                    "message": "Successfully created a physical subnet '{0}'for vpc '{1}' in host '{2}'".format(ip_address, vpc_id, vpc.host),
                    #"dbMessage": db_result,
                    "success": True
                }
            else:
                return {
                    "message": "Unable to physically create subnet '{0}' for vpc {1} (id is {2})".format(ip_address, vpc.vpcName, vpc_id),
                    "success": False
                }

    def ensure_valid_ip_network(self, subnet_str):
        try:
            valid_ip_network = ipaddress.IPv4Interface(subnet_str).network
            print(valid_ip_network)
            print(subnet_str)
            if str(valid_ip_network) != subnet_str:
                return False, valid_ip_network
            else:
                return True, None
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)
            return False, None

    def create_physically(self, ip_address, vpc_id, host, scaleFactor):
        result = False
        host = host.lower()

        subnet_id = self.db.get_next_subnet_id()
        if subnet_id < 0:
            return {"message": "A SQL error occured in creating subnet '{0}'".format(ip_address), "success": False}

        try:
            json_obj = {}
            json_obj["subnet_id"] = subnet_id
            json_obj["vpc_id"] = vpc_id
            json_obj["edge_count"] = scaleFactor
            
            if ip_address:  
                json_obj["ip_address"] = ip_address

            vars_json = json.dumps(json_obj)
            commands = [
                "sudo",
                "ansible-playbook",
                "-i",
                "hosts.ini",
                "create-subnet.yml",
                "-l {0}".format(host),
                "-e",
                vars_json
            ]
            p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
            p.wait()
            # print("stderr", stderr)
            # print("retcode =", p.returncode)
            if p.returncode != 0:
                print(
                    "\r\nUnable to run ansible 'create-subnet.yml' for subnet '{0}' in VPC '{1}'\r\n".format(ip_address, vpc_id))
                return False

            result = True
        except Exception as e:
            print(
                "\r\nUnable to physically create the subnet '{0}' for vpc id '{1}'\r\nException below:\r\n{2}".format(ip_address, vpc_id, e))
            result = False

        return result

    def create_in_db(self, vpc_id, ip_address, subnet_name) -> int:

        # create vpc in db
        subnetId_str = self.db.create_subnet(ip_address, subnet_name, vpc_id)
        if(subnetId_str != None):
            return int(subnetId_str)
        else:
            return -1

    def delete_subnet(self, args):
        customer_id = args["customerId"]
        vpc_id = args["vpcId"]
        subnet_id = args["subnetId"]

        # ensure valid customer
        if (self.db.get_customer_by_id(customer_id) == None):
            return {"message": "No customer found with id '{0}'".format(customer_id), "success": False}

        # ensure valid vpc
        vpc = self.db.get_vpc_by_id(vpc_id, customer_id)
        if(vpc == None):
            return {"message": "No vpc found with id '{0}' for customer '{1}'".format(vpc_id, customer_id), "success": False}

        # get subnet
        subnet = self.db.get_subnet_by_id(subnet_id, vpc_id)
        if subnet == None:
            return {"message": "No subnet found with id '{0}' for vpc '{1}'".format(subnet_id, vpc_id), "success": False}

        # Check for no VMs ...and then delete subnets
        vm_list = self.db.get_all_vms(subnet_id)
        if len(vm_list) > 0:
            return {
                "vmList": vm_list,
                "message": "Please delete these VMs (id list given) first!",
                "success": False
            }

        # ...NO VMs were found...

        # delete subnet physically
        phy_result = self.delete_physically(subnet.subnetId, vpc_id, vpc.host)

        # save in db if successful
        if phy_result:
            return self.delete_in_db(subnet_id, subnet.ipAddress, vpc_id, vpc.host)
        else:
            return {
                "message": "Unable to physically delete subnet '{0}' for vpc '{1}' in host '{2}'".format(subnet.ipAddress, vpc_id, vpc.host),
                "success": False
            }

    def delete_physically(self, subnet_id, vpc_id, host):
        # call southbound to delete subnet
        result = False
        host = host.lower()

        try:
            json_obj = {}
            json_obj["subnet_id"] = subnet_id
            json_obj["vpc_id"] = vpc_id

            vars_json = json.dumps(json_obj)
            commands = [
                "sudo",
                "ansible-playbook",
                "-i",
                "hosts.ini",
                "delete-subnet.yml",
                "-l {0}".format(host),
                "-e",
                vars_json
            ]
            p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
            p.wait()
            # print("stderr", stderr)
            # print("retcode =", p.returncode)
            if p.returncode != 0:
                print(
                    "\r\nUnable to run ansible 'delete-subnet.yml' for subnet '{0}' in VPC '{1}'\r\n".format(subnet_id, vpc_id))
                return False

            result = True
        except Exception as e:
            print(
                "\r\nUnable to physically create the subnet '{0}' for vpc id '{1}'\r\nException below:\r\n{2}".format(subnet_id, vpc_id, e))
            result = False

        return result

    def delete_in_db(self, subnet_id, ip_address, vpc_id, host):
        # delete subnet in db
        delete_ok = self.db.delete_subnet(subnet_id)
        if(delete_ok):
            return {
                "message": "subnet '{0}' is deleted from host '{1}'".format(
                    ip_address, host),
                "success": True
            }
        else:
            return {
                "message": "failed to delete subnet '{0}' from host '{1}'".format(
                    ip_address, host),
                "success": False
            }

