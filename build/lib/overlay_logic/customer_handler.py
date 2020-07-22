from overlay_north.provider_db import ProviderDb


class CustomerHandler:
    def __init__(self):
        self.SOUTHBOUND_DIRECTORY = 'overlay_south'
        self.db = ProviderDb()

    def create_customer(self, args):
        customerName = args["customerName"]

        db_result = self.create_in_db(customerName)
        return db_result

    def create_in_db(self, customer_name):
         # check db to see if vpc exists...
        if(self.db.get_customer(customer_name) != None):
            return {"message": "customer '{0}' already exists".format(customer_name), "success": False}

        # create customer in db
        customerId_str = self.db.create_customer(customer_name)
        if(customerId_str != None):
            return {"message": "customer created. Id is '{0}'".format(customerId_str), "success": True}
        else:
            return {"message": "failed to create customer '{0}'".format(customer_name), "success": False}

    def get_all_customers(self):
        # No args required...
        return self.db.get_all_customers()

    def delete_customer(self, args):
        customer_name = args["customerName"]
        customer = self.db.get_customer(customer_name)

        if(customer == None):
            return {"message": "No customer with name '{0}' found".format(customer_name), "success": False}

        errors = {}

        # This should delete VPCs, Subnets, VMs, the whole works!
        # get ALL the vpc for customer

        vpc_list = self.db.get_all_vpcs(customer.customerId)
        if len(vpc_list) > 0:
            return {
                "message": "Please delete these VPCs first! --> '{0}'".format(vpc_list),
                "success": False
            }

        # delete customer
        if not self.db.delete_customer(customer.customerId):
            mess = {"message": "Failed to delete customer with id '{0}'".format(
                customer.customerId)}
            errors.append(mess)

        if len(errors) == 0:
            return {
                "message": "Successfully deleted customer '{0}'".format(customer.customerName),
                "success": True,
                "notice": "Customer '{0}' does not exist anymore!".format(customer.customerName)
            }
        else:
            return {
                "message": "Failed to delete ALL of customer '{0}'".format(customer.customerName),
                "success": False,
                "errors": errors
            }
