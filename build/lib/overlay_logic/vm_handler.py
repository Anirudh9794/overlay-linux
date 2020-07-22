import sys
import subprocess
from overlay_north.python_models import vm_model
from overlay_north.provider_db import ProviderDb
import random
import json
import ipaddress

SOUTHBOUND_DIRECTORY = 'overlay_south'
PLAYBOOK_COMMAND = 'ansible-playbook'
CREATE_VM_PLAYBOOK = 'create-vm.yml'


class VMHandler():
    def __init__(self):
        self.db = ProviderDb()
        self.SOUTHBOUND_DIRECTORY = 'overlay_south'

    def create_vm(self, args):
        customer_id = args['customerId']
        vpc_id = args['vpcId']
        subnet_id = args['subnetId']
        vm_name = args['vmName']

        # verify customer id
        if (self.db.get_customer_by_id(customer_id) == None):
            return {"message": "No customer found with id '{0}'".format(customer_id), "success": False}

        # verify vpc id
        vpc = self.db.get_vpc_by_id(vpc_id, customer_id)
        if(vpc == None):
            return {"message": "No vpc found with id '{0}' for customer '{1}'".format(vpc_id, customer_id), "success": False}

        # verify subnet id
        subnet = self.db.get_subnet_by_id(subnet_id, vpc_id)
        if(subnet == None):
            return {"message": "failed to get subnet id '{0}' for vpc id '{1}'".format(subnet_id, vpc_id), "success": False}

        # check db to see if VM exists...
        if(self.db.get_vm(vm_name, subnet_id) != None):
            return {
                "message": "vm '{0}' already exists in subnet '{1}'".format(vm_name, subnet_id),
                "success": False
            }

        # ...NO VM exists at this point...

        # create MAC address
        mac_addr = self.generate_mac_addr()

        # create IP address
        do_not_use_ip_list = self.db.get_all_vm_ip_addrs(subnet_id)
        ip_addr = self.generate_ip_addr(subnet.ipAddress, do_not_use_ip_list)

        if ip_addr == None:
            return {
                "message": "No more ip addresses available for subnet '{0}' (id: '{1}') in vpc '{2}'".format(subnet.ipAddress, subnet.subnetId, vpc.vpcName),
                "success": False
            }

        # create unique vm name
        vm_id = self.db.get_next_vm_id()
        if vm_id < 0:
            return {"message": "A SQL error occured in creating VM '{0}'".format(vm_name), "success": False}
        unique_vm_name = "{0}_{1}".format(vm_name, str(vm_id))

        # create vm physically
        phy_result = self.create_physically(vm_id,
                                            unique_vm_name, mac_addr, ip_addr, subnet_id, vpc_id, vpc.host)

        # save in db if successful
        if phy_result:
            return self.create_in_db(unique_vm_name, mac_addr, ip_addr, subnet_id, vpc_id)
        else:
            return {
                "message": "Unable to physically create vm '{0}' for subnet {1}".format(vm_name, subnet_id),
                "success": False
            }

    def create_physically(self, vmId, vmName, macAddr, ipAddr, subnetId, vpcId, host):
        # # TODO: Fix this!
        # return True

        args = {"guests": [{"name": vmName, "subnet_id": subnetId,
                            "vpc_id": vpcId, "vm_id": vmId, "mac_address": macAddr}]}
        commands = [
            "sudo",
            "ansible-playbook",
            "create-vms.yml",
            "-i",
            "hosts.ini",
            "-e",
            json.dumps(args),
            "-l {0}".format(host.lower())
        ]
        p = subprocess.Popen(commands, cwd=self.SOUTHBOUND_DIRECTORY)
        p.wait()

        if p.returncode != 0:
            print(
                "\r\nUnable to run ansible 'create-vms.yml' in vm_handler.create_physically\r\n")
            return False
        else:
            return True

    def generate_mac_addr(self) -> str:
        mac = [0x08, 0x00, 0x22,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)
               ]

        return ':'.join(map(lambda x: "%02x" % x, mac))

    def generate_ip_addr(self, subnet_ip: str, do_not_use_ip_list: list) -> str:
        # subnet_ip ex: "192.168.2.0/28"
        ip_range = ipaddress.IPv4Network(subnet_ip)
        network_addr = str(ip_range.network_address)
        broadcast_addr = str(ip_range.broadcast_address)
        the_ip_addr = None

        for ip in ip_range.hosts():
            ip_str = str(ip)

            if ip_str == network_addr:
                print("Network IP '{0}' cannot be used".format(ip_str))
                continue

            # do not return an already used IP!
            if ip_str in do_not_use_ip_list:
                print("IP '{0}' is already used".format(ip_str))
                continue

            if ip_str == broadcast_addr:
                print("Broadcast IP '{0}' cannot be used".format(ip_str))
                continue

            print("IP to be assigned to vm is: '{0}'\r\n".format(ip_str))
            return ip_str

    def create_in_db(self, vm_name, mac_addr, ip_addr, subnet_id, vpc_id):
        vm_id_str = self.db.create_vm(
            vm_name, mac_addr, ip_addr, subnet_id, vpc_id)
        if(vm_id_str != None):
            return {"message": "Vm '{0}' (ID '{1}', ip '{2}') created in subnet '{3}'.".format(vm_name, vm_id_str, ip_addr, subnet_id),
                    "success": True}
        else:
            return {"message": "failed to add in db the vm '{0}' (ip '{1}') in subnet '{2}'".format(vm_name, ip_addr, subnet_id), "success": False}

    def delete_vm(self, args):
        customer_name = args['customerName']
        vmNames = args['vmNames']  # a list

        output = {}
        output["notice"] = []
        output["success"] = False

        for vm_str_obj in vmNames:
            # convert str to dict
            vm_str_obj = vm_str_obj.replace("\'", "\"")
            vm = json.loads(vm_str_obj)
            print(vm)

            host = vm["host"]
            vm_name = vm["vmName"]
            vm_ip = vm["vmIp"]
            subnet_ip = vm["subnetIp"]
            vpc_name = vm["vpcName"]

            # get vpc
            vpc = self.db.get_vpc(vpc_name, customer_name, host)
            if vpc == None:
                output["notice"].append(
                    {
                        "message": "No vpc found with name '{0}' for customer '{1}' in host '{2}'".format(
                            vpc_name, customer_name, host),
                        "success": False
                    })
                continue
            else:
                vpc_id = vpc.vpcId

            # get subnet
            subnet = self.db.get_subnet(subnet_ip, vpc_id)
            if subnet == None:
                output["notice"].append(
                    {
                        "message": "No subnet '{0}' found in vpc '{1}' (vpc id={2}) in host '{3}'".format(
                            subnet_ip, vpc.vpcName, vpc.vpcId, host),
                        "success": False
                    })
                continue
            else:
                subnet_id = subnet.subnetId

            vm = self.db.get_vm(vm_name, subnet.subnetId)
            if(vm == None):
                output["notice"].append(
                    {
                        "message": "No VM '{0}' found in subnet '{1}' (subnet id={2}) in vpc '{3}'".format(
                            vm_name, subnet_ip, subnet.subnetId, vpc.vpcName),
                        "success": False
                    })
                continue
            else:
                vm_id = vm.vmId

            phy_result = self.delete_physically(host, vm_name, vm_ip)

            if phy_result:
                db_result = self.delete_in_db(
                    vm_id, vm_name, subnet_ip, vpc_name)

                if db_result:
                    output["notice"].append({
                        "message": "Successfully deleted vm {0} in subnet '{1}' (subnet id={2}) in vpc '{3}'".format(vm_name, subnet_ip, subnet.subnetId, vpc.vpcName),
                        "dbMessage": db_result,
                        "success": True
                    })
                    output["success"] = True

                else:
                    output["notice"].append({
                        "message": "Failed to delete vm {0} in subnet '{1}' (subnet id={2}) in vpc '{3}'".format(vm_name, subnet_ip, subnet.subnetId, vpc.vpcName),
                        "dbMessage": db_result,
                        "success": False
                    })
                    output["success"] = False

            else:
                output["notice"].append(
                    {
                        "message": "Failed to physically delete VM {0} with ip {1} in host {2}".format(vm_name, vm_ip, host),
                        "success": False
                    }
                )
                output["success"] = False

        return output

    def delete_physically(self, host, vm_name, vm_ip):
        return True  # TODO: Fix this!

    def delete_in_db(self, vm_id, vm_name, subnet_ip, vpc_name):
        delete_ok = self.db.delete_vm(vm_id)
        if(delete_ok):
            results = {
                "message": "vm '{0}' is deleted from subnet '{1}' in vpc {2}".format(
                    vm_name, subnet_ip, vpc_name),
                "success": True
            }
        else:
            results = {
                "message": "Failed to delete vm '{0}' from subnet '{1}' in vpc {2}".format(
                    vm_name, subnet_ip, vpc_name),
                "success": False
            }

        return results
