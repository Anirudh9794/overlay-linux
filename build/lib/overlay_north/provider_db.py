import mysql.connector as mysql
from overlay_north.python_models import vpc_model
from overlay_north.python_models import subnet_model
from overlay_north.python_models import vm_model
from overlay_north.python_models import customer_model
from overlay_north.python_models import transit_model
from overlay_north.python_models import tunnel_model
import os
from typing import List
import traceback


class ProviderDb:
    def __init__(self):
        self.db = self.connect_db()
        self.dir_path = os.path.dirname(os.path.realpath(__file__))

    def connect_db(self):
        db = mysql.connect(
            host="ece792-db.cdfbjtoqs7wa.us-east-2.rds.amazonaws.com",
            user="admin",
            passwd="password"
            #host="127.0.0.1",
            #user="admin",
            #passwd="password",
        )
        return db

    # ======== Create Functions ===========

    def create_db(self):
        sqlPath = self.dir_path + "/sql/db.sql"

        try:
            with open(sqlPath, 'r') as _file:
                sql = _file.read().replace('\n', '')
        except Exception as e:
            print(
                "\r\nNo db.sql file found in '{0}'. Ensure file exists!\r\n".format(sqlPath))
            return False

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)

            self.db = mysql.connect(
                host="ece792-db.cdfbjtoqs7wa.us-east-2.rds.amazonaws.com",
                user="admin",
                passwd="password",
                database='ece792-db'
            )
            return True
        except Exception as e:
            print("\r\nUnable to create ece792-db! Connection error?\r\n")
            return False

    def create_tables(self):
        if not self.create_db():
            return False
        sqlPath = self.dir_path + "/sql"
        # must be in order!
        files = ["customer_table.sql", "vpc_table.sql", "subnet_table.sql",
                 "vm_table.sql", "transit_table.sql", "tunnel_table.sql"]

        for _fileName in files:
            file = sqlPath + "/" + _fileName
            with open(file, 'r') as _file:
                sql = _file.read().replace('\n', '')

            try:
                mycursor = self.db.cursor()
                mycursor.execute(sql)
            except Exception as e:
                print(
                    "\r\nUnable to create table from sql {0}\r\n".format(file))
                traceback.print_exception(type(e), e, e.__traceback__)
                return False

        return True

    def create_customer(self, customerName) -> str:
        sql = "INSERT INTO `ece792-db`.`customer_table`(customerName) VALUES (%s)"
        val = (customerName,)
        print(sql % val)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql, val)
            self.db.commit()
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.create_customer\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

        if(mycursor.rowcount > 0):
            customer = self.get_customer(customerName)
            return str(customer.customerId)

        return None

    def create_vpc(self, vpc_name, customer_id, host, scale_factor) -> str:
        sql = """INSERT INTO `ece792-db`.`vpc_table` (vpcName, customerId, host, scaleFactor) VALUES (%s, %s, %s, %s)"""
        val = (vpc_name, customer_id, host.lower(), scale_factor)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql, val)
            self.db.commit()
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.create_vpc\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

        if(mycursor.rowcount > 0):
            vpc = self.get_vpc(vpc_name, customer_id, host)
            return str(vpc.vpcId)
        else:
            return None

    def create_subnet(self, ipAddress, subnetName, vpcId) -> str:
        sql = """INSERT INTO `ece792-db`.`subnet_table` (ipAddress, subnetName, vpcId) VALUES (%s, %s, %s)"""
        val = (ipAddress, subnetName, vpcId)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql, val)
            self.db.commit()
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.create_subnet\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

        if(mycursor.rowcount > 0):
            subnet = self.get_subnet(ipAddress, vpcId)
            return str(subnet.subnetId)
        else:
            return None

    def create_vm(self, vmName, macAddr, ipAddr, subnetId, vpcId):
        sql = """INSERT INTO `ece792-db`.`vm_table` (vmName, macAddr, ipAddr, subnetId, vpcId) VALUES ( %s, %s, %s, %s, %s)"""
        val = (vmName, macAddr, ipAddr, subnetId, vpcId)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql, val)
            self.db.commit()
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.create_vm\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

        if(mycursor.rowcount > 0):
            vm = self.get_vm(vmName, subnetId)
            return str(vm.vmId)
        else:
            return None

    def create_transit(self, customer_id, host, reliability_factor) -> str:
        sql = """INSERT INTO `ece792-db`.`transit_table` (customer_id, host, reliability_factor) VALUES (%s, %s, %s)"""
        val = (customer_id, host, reliability_factor)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql, val)
            self.db.commit()
            return self.get_transit(customer_id).transit_id
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.create_transit\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return "-1"

    def create_tunnel(self, transit_id, vpc_id, tunnel_type) -> int:
        sql = """INSERT INTO `ece792-db`.`tunnel_table` (transit_id, vpc_id, tunnel_type) VALUES (%s, %s, %s)"""
        val = (transit_id, vpc_id, tunnel_type)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql, val)
            self.db.commit()
            return int(mycursor.lastrowid)  # very interesting...
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.create_tunnel\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return -1

    # ======== Get Functions ===========

    def get_customer(self, customerName) -> customer_model.Customer:
        sql = """SELECT * FROM `ece792-db`.`customer_table`
            WHERE customerName = '{0}';""".format(customerName)
        rows = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_customer\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

        if len(rows) == 0:
            return None

        row = rows[0]
        __customerId = row[0]
        __customerName = row[1]

        customer = customer_model.Customer(__customerId, __customerName)
        return customer

    def get_customer_by_id(self, customer_id) -> customer_model.Customer:
        sql = """SELECT * FROM `ece792-db`.`customer_table`
            WHERE customerId = '{0}';""".format(customer_id)
        rows = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_customer_by_id\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

        if len(rows) == 0:
            return None

        row = rows[0]
        __customerId = row[0]
        __customerName = row[1]

        return customer_model.Customer(__customerId, __customerName)

    def get_all_customers(self) -> list:
        sql = """SELECT * FROM `ece792-db`.`customer_table`;"""
        rows = []
        customers = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_customer\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)

        if len(rows) == 0:
            return []

        for row in rows:
            __customerId = row[0]
            __customerName = row[1]
            __customer = {"customerId": __customerId,
                          "customerName": __customerName}
            customers.append(__customer)  # cannot serialize Customer...

        return customers

    def get_next_vpc_id(self):
        sql = """SELECT `auto_increment` FROM INFORMATION_SCHEMA.TABLES WHERE table_name = 'vpc_table';"""
        # sql = """SELECT MAX(vpcId) FROM `ece792-db`.`vpc_table`;"""
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            row = mycursor.fetchone()
            lastId = row[0]
            if lastId == None:
                return 0
            else:
                return lastId
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_next_vpc_id\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return -1

    def get_vpc_by_id(self, vpc_id, customer_id) -> vpc_model.VPC:
        sql = """SELECT * FROM `ece792-db`.`vpc_table`
            WHERE vpcId = '{0}' AND customerId = '{1}';""".format(vpc_id, customer_id)
        rows = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_vpc\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

        if(len(rows) == 0):
            return None

        # get row values
        row = rows[0]
        __vpcId = row[0]  # ex. row[0] is vpcId
        __vpcName = row[1]
        __customerId = row[2]
        __host = row[3]
        __scaleFactor = row[4]

        # return vpc
        vpc = vpc_model.VPC(__vpcId, __vpcName,
                            __customerId, __host, __scaleFactor)
        return vpc

    def get_vpc(self, vpc_name, customer_id, host) -> vpc_model.VPC:
        sql = """SELECT * FROM `ece792-db`.`vpc_table`
            WHERE vpcName = '{0}' AND customerId = '{1}' AND host = '{2}';""".format(vpc_name, customer_id, host.lower())
        # print("\r\n the sql in getvpc is \r\n{0}\r\n".format(sql))
        rows = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
            # print("rows length is: {0}".format(len(rows)))
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_vpc\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

        if(len(rows) == 0):
            return None

        # get row values
        row = rows[0]
        __vpcId = row[0]  # ex. row[0] is vpcId
        __vpcName = row[1]
        __customerId = row[2]
        __host = row[3]
        __scaleFactor = row[4]

        # return vpc
        vpc = vpc_model.VPC(__vpcId, __vpcName,
                            __customerId, __host, __scaleFactor)
        return vpc

    def get_all_vpcs(self, customer_id) -> List[str]:
        sql = """SELECT * FROM `ece792-db`.`vpc_table`
            WHERE customerId = '{0}';""".format(customer_id)

        rows = []
        vpc_list = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_vpc_list\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)

        for row in rows:
            __vpcId = row[0]  # ex. row[0] is vpcId
            vpc_list.append(__vpcId)

        return vpc_list

    def get_subnet(self, subnetIp, vpcId) -> subnet_model.Subnet:
        sql = """SELECT * FROM `ece792-db`.`subnet_table`
            WHERE ipAddress = '{0}' AND vpcId = '{1}';""".format(subnetIp, vpcId)
        rows = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
            # print("rows length is: {0}".format(len(rows)))
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_subnet\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

        if(len(rows) == 0):
            return None

        # get row values
        row = rows[0]
        __subnetId = row[0]  # ex. row[0] is subnetId
        __ipAddress = row[1]
        __subnetName = row[2]
        __vpcId = row[3]

        # return subnet
        subnet = subnet_model.Subnet(
            __subnetId, __vpcId, __ipAddress, __subnetName)
        return subnet

    def get_subnet_by_id(self, subnet_id, vpc_id) -> subnet_model.Subnet:
        sql = """SELECT * FROM `ece792-db`.`subnet_table`
            WHERE subnetId = '{0}' AND vpcId = '{1}';""".format(subnet_id, vpc_id)
        rows = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_subnet_by_id\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

        if(len(rows) == 0):
            return None

        # get row values
        row = rows[0]
        __subnetId = row[0]  # ex. row[0] is subnetId
        __ipAddress = row[1]
        __subnetName = row[2]
        __vpcId = row[3]

        # return subnet
        subnet = subnet_model.Subnet(
            __subnetId, __vpcId, __ipAddress, __subnetName)
        return subnet

    def get_all_subnets(self, vpc_id) -> List[subnet_model.Subnet]:
        sql = """SELECT ipAddress FROM `ece792-db`.`subnet_table`
            WHERE vpcId = '{0}';""".format(vpc_id)

        subnets = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            ip_rows = mycursor.fetchall()

            print("There are '{0}' ip rows returned in get_all_subnets".format(
                len(ip_rows)))

            for row in ip_rows:
                ip_address = row[0]
                subnet = self.get_subnet(ip_address, vpc_id)
                subnets.append(subnet)

        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_all_subnets")
            traceback.print_exception(type(e), e, e.__traceback__)
            return []

        return subnets

    def get_all_subnets_ip(self, vpc_id) -> List[str]:
        sql = """SELECT ipAddress FROM `ece792-db`.`subnet_table`
            WHERE vpcId = '{0}';""".format(vpc_id)

        subnet_ip_list = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            ip_rows = mycursor.fetchall()

            print("There are '{0}' ip rows returned in get_all_subnets_ip".format(
                len(ip_rows)))

            for row in ip_rows:
                ip_address = row[0]
                subnet_ip_list.append(ip_address)

        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_all_subnets_ip")
            traceback.print_exception(type(e), e, e.__traceback__)
            return []

        return subnet_ip_list

    def get_transit(self, customer_id) -> transit_model.Transit_Model:
        sql = """SELECT * FROM `ece792-db`.`transit_table`
            WHERE customer_id = '{0}';""".format(customer_id)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)

            _rows = mycursor.fetchall()
            if(len(_rows) == 0):
                return None

            row = _rows[0]
            transit_id = row[0]
            customer_id = row[1]
            host = row[2]
            reliability_factor = row[3]
            # tunnels is an object...
            tunnels = self.get_all_tunnels_by_transit_id(transit_id)

            return transit_model.Transit_Model(transit_id, customer_id, host, reliability_factor, tunnels)

        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_transit")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

    def get_tunnel(self, tunnel_id) -> tunnel_model.Tunnel_Model:
        sql = """SELECT * FROM `ece792-db`.`tunnel_table` WHERE tunnel_id = '{0}';""".format(
            tunnel_id)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)

            _rows = mycursor.fetchall()
            if(len(_rows) == 0):
                return None

            row = _rows[0]
            _tunnel_id = row[0]
            _transit_id = row[1]
            _vpc_id = row[2]
            _tunnel_type = row[3]

            return tunnel_model.Tunnel_Model(_tunnel_id, _transit_id, _vpc_id, _tunnel_type)

        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_tunnel")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

    def get_vm(self, vmName, subnetId) -> vm_model.VM_Model:
        sql = """SELECT * FROM `ece792-db`.`vm_table`
            WHERE vmName = '{0}' AND subnetId = '{1}';""".format(vmName, subnetId)
        rows = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_vm\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

        if(len(rows) == 0):
            return None

        # get row values
        row = rows[0]
        __vmId = row[0]
        __vmName = row[1]
        __vpcName = row[2]
        __subnetId = row[3]

        # return subnet
        return vm_model.VM_Model(
            __vmId, __vmName, __vpcName, __subnetId)

    def get_next_subnet_id(self):
        sql = """SELECT `auto_increment` FROM INFORMATION_SCHEMA.TABLES WHERE table_name = 'subnet_table';"""
        # sql = """SELECT MAX(subnetId) FROM `ece792-db`.`subnet_table`;"""
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            row = mycursor.fetchone()
            lastId = row[0]
            if lastId == None:
                return 0
            else:
                return lastId
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_next_subnet_id\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return -1

    def get_next_vm_id(self):
        sql = """SELECT `auto_increment` FROM INFORMATION_SCHEMA.TABLES WHERE table_name = 'vm_table';"""
        # sql = """SELECT MAX(vmId) FROM `ece792-db`.`vm_table`;"""

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            lastId = mycursor.fetchone()[0]
            if lastId == None:
                return 0
            else:
                return lastId
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_next_vm_id\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return -1

    def get_next_transit_id(self):
        sql = """SELECT `auto_increment` FROM INFORMATION_SCHEMA.TABLES WHERE table_name = 'transit_table';"""
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            lastId = mycursor.fetchone()[0]
            if lastId == None:
                return 0
            else:
                return lastId
        except Exception as e:
            print(
                "\r\nUnable to execute sql in provider_db.get_next_transit_id\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return -1

    def get_next_tunnel_id(self):
        sql = """SELECT `auto_increment` FROM INFORMATION_SCHEMA.TABLES WHERE table_name = 'tunnel_table';"""
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            lastId = mycursor.fetchone()[0]
            if lastId == None:
                return 0
            else:
                return lastId
        except Exception as e:
            print(
                "\r\nUnable to execute sql in provider_db.get_next_tunnel_id\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return -1

    def get_all_vms(self, subnet_id) -> List[str]:
        sql = """SELECT vmId FROM `ece792-db`.vm_table WHERE subnetId = '{0}';""".format(
            subnet_id)

        vm_id_list = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
            for row in rows:
                vm_id = row[0]
                vm_id_list.append(vm_id)

        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_all_vms\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            vm_id_list = []

        return vm_id_list

    def get_all_vm_ip_addrs(self, subnet_id) -> List[str]:

        sql = """SELECT ipAddr FROM `ece792-db`.vm_table WHERE subnetId = '{0}';""".format(
            subnet_id)

        vm_ip_list = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
            for row in rows:
                vm_ip = row[0]
                vm_ip_list.append(vm_ip)

        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_all_vm_ip_addrs\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            vm_ip_list = []

        return vm_ip_list

    def get_all_tunnels_by_transit_id(self, transit_id) -> List[tunnel_model.Tunnel_Model]:
        sql = """SELECT * FROM `ece792-db`.tunnel_table WHERE transit_id = '{0}';""".format(
            transit_id)

        tunnel_list = []
        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
            for row in rows:
                tunnel_id = row[0]
                transit_id = row[1]
                vpc_id = row[2]
                tunnel_type = row[3]

                tunnel = tunnel_model.Tunnel_Model(
                    tunnel_id, transit_id, vpc_id, tunnel_type)
                # tunnel = {"tunnelId": tunnel_id, "transitId": transit_id, "vpcId": vpc_id, "tunnelType": tunnel_type}
                tunnel_list.append(tunnel)

        except Exception as e:
            print(
                "\r\nUnable to execute sql in provider_db.get_all_tunnels_by_transit_id\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            tunnel_list = []

        return tunnel_list

    def get_transit_router_host(self, customer_id) -> str:
        sql = """SELECT host from `ece792-db`.transit_router_table WHERE customerId = '{0}';"""
        rows = []

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            rows = mycursor.fetchall()
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.get_transit_router_host\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return None

        if(len(rows) == 0):
            return None

        # get row values
        row = rows[0]

        return str(row[4])  # host is column 5

    # ======== Delete Functions ===========

    def delete_customer(self, customer_id) -> bool:
        sql = """DELETE FROM `ece792-db`.`customer_table` WHERE (`customerId` = '{0}');""".format(
            customer_id)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            self.db.commit()
            count = mycursor.rowcount
            print("delete customer id result: {0}".format(count))
            if int(count) == 1:
                return True
            else:
                print(
                    "Unable to delete a single row from the customer table! Either deleted no rows or multiple rows!")
                return False
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.delete_customer\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return False

    def delete_subnet(self, subnet_id) -> bool:
        sql = """DELETE FROM `ece792-db`.`subnet_table` WHERE (`subnetId` = '{0}');""".format(
            subnet_id)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            self.db.commit()
            count = mycursor.rowcount
            print("delete subnet id result: {0}".format(count))
            if int(count) == 1:
                return True
            else:
                print(
                    "Unable to delete a single row from the subnet table! Either deleted no rows or multiple rows!")
                return False
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.delete_subnet\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return False

    def delete_vpc(self, vpc_id) -> bool:
        sql = """DELETE FROM `ece792-db`.`vpc_table` WHERE (`vpcId` = '{0}');""".format(
            vpc_id)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            self.db.commit()
            count = mycursor.rowcount
            print("delete vpc id result: {0}".format(count))
            if int(count) == 1:
                return True
            else:
                print(
                    "Unable to delete a single row from the vpc table! Either deleted no rows or multiple rows!")
                return False
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.delete_vpc\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return False

    def delete_vm(self, vm_id) -> bool:
        sql = """DELETE FROM `ece792-db`.`vm_table` WHERE (`vmId` = '{0}');""".format(
            vm_id)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            self.db.commit()
            count = mycursor.rowcount
            print("delete vm result: {0}".format(count))
            if int(count) == 1:
                return True
            else:
                print(
                    "Unable to delete a single row from the vm table! Either deleted no rows or multiple rows!")
                return False
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.delete_vm\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return False

    def delete_transit(self, customer_id) -> bool:
        sql = """DELETE FROM `ece792-db`.`transit_table` WHERE (`customer_id` = '{0}');""".format(
            customer_id)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            self.db.commit()
            count = mycursor.rowcount
            if int(count) == 1:
                return True
            else:
                print(
                    "Unable to delete a single row from the transit table! Either deleted no rows or multiple rows!")
                return False
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.delete_vpc\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return False

    def delete_tunnel(self, tunnel_id) -> bool:
        sql = """DELETE FROM `ece792-db`.`tunnel_table` WHERE (`tunnel_id` = '{0}');""".format(
            tunnel_id)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            self.db.commit()
            count = mycursor.rowcount
            if int(count) == 1:
                return True
            else:
                print(
                    "Unable to delete a single row from the tunnel table! Either deleted no rows or multiple rows!")
                return False
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.delete_tunnel\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return False

    def bulk_delete_vm(self, subnet_id) -> int:
        sql = """DELETE FROM `ece792-db`.`vm_table` WHERE (`subnetId` = '{0}');""".format(
            subnet_id)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            self.db.commit()
            count = mycursor.rowcount
            print("bulk_delete_vm result: {0}".format(count))
            return count
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.bulk_delete_vm\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return -1

    def bulk_delete_subnet(self, vpc_id) -> int:
        sql = """DELETE FROM `ece792-db`.`subnet_table` WHERE (`vpcId` = '{0}');""".format(
            vpc_id)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            self.db.commit()
            count = mycursor.rowcount
            print("bulk_delete_subnet result: {0}".format(count))
            return count
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.bulk_delete_subnet\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return -1

    def bulk_delete_vpc(self, customer_id) -> int:
        sql = """DELETE FROM `ece792-db`.`vpc_table` WHERE (`customerId` = '{0}');""".format(
            customer_id)

        try:
            mycursor = self.db.cursor()
            mycursor.execute(sql)
            self.db.commit()
            count = mycursor.rowcount
            print("bulk_delete_vpc result: {0}".format(count))
            return count
        except Exception as e:
            print("\r\nUnable to execute sql in provider_db.bulk_delete_vpc\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            return -1

    def delete_all_tables(self):
        result = {}
        print("inside db restart scratch")

        sql_stmts = [
            """DROP TABLE `ece792-db`.`vpc_table`;""",
            """DROP TABLE `ece792-db`.`subnet_table`;""",
            """DROP TABLE `ece792-db`.`vm_table`;"""
        ]

        try:
            for sql in sql_stmts:
                mycursor = self.db.cursor()
                mycursor.execute(sql)
                result["success"] = True
        except Exception as e:
            print(
                "\r\nUnable to successfully delete all tables in provider_db.restart_from_scratch\r\n")
            traceback.print_exception(type(e), e, e.__traceback__)
            result["success"] = False

        return result

