from flask import jsonify, Response, request
from flask_restful import Resource, reqparse, abort
from overlay_logic.subnet_handler import SubnetHandler
from http import HTTPStatus


class Subnet_Controller(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('customerId')
        self.parser.add_argument('vpcId')
        self.parser.add_argument('subnet')
        self.parser.add_argument('subnetId')

        self.handler = SubnetHandler()

    def post(self):
        args = self.parser.parse_args()

        output = self.handler.create_subnet(args)
        resp = jsonify(output)

        return resp

    def delete(self):
        args = self.parser.parse_args()

        output = self.handler.delete_subnet(args)
        resp = jsonify(output)

        if output["success"] == True:
            resp.status_code = HTTPStatus.OK
        else:
            resp.status_code = HTTPStatus.BAD_REQUEST

        return resp

    def get(self):
        args = request.args  # To get query params in URL

        if not args or not args["customerId"]:
            output = {
                "message": "No customer id passed in as query parameter. For example, put this at the of the URL: ...?customerId=1",
                "success": False
            }
        else:
            output = self.handler.get_all_subnets(args)

        resp = jsonify(output)
        return resp
