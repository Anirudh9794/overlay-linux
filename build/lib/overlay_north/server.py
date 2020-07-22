import sys
from flask import Flask, jsonify
from flask_restful import Api
# from .vm import VM
from .api_controllers.vpc_controller import VPC_Controller
from .api_controllers.vm_controller import VM_Controller
from .api_controllers.subnet_controller import Subnet_Controller
from .api_controllers.config_controller import Config_Controller
from .api_controllers.transit_controller import Transit_Controller
from .api_controllers.tunnel_controller import Tunnel_Controller
from .api_controllers.customer_controller import Customer_Controller

app = Flask(__name__, static_url_path="")
api = Api(app)


api.add_resource(Customer_Controller, '/customer')
api.add_resource(VPC_Controller, '/vpc')
api.add_resource(VM_Controller, '/vm')
api.add_resource(Subnet_Controller, '/subnet')
api.add_resource(Transit_Controller, '/transit')
api.add_resource(Tunnel_Controller, '/tunnel')
api.add_resource(Config_Controller, '/config')
