import sys
from flask import jsonify, Response, request
from flask_restful import Resource, reqparse, abort
from overlay_logic.vpc_handler import VPCHandler
from http import HTTPStatus
from overlay_north.python_models import vpc_model


class VPC_Controller(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('vpcId')
        self.parser.add_argument('vpcName')
        self.parser.add_argument('host')
        self.parser.add_argument('customerId')
        self.parser.add_argument('scaleFactor')

        self.handler = VPCHandler()

    def post(self):
        args = self.parser.parse_args()

        output = self.handler.create_vpc(args)
        resp = jsonify(output)

        if output["success"] == True:
            resp.status_code = HTTPStatus.CREATED
        else:
            resp.status_code = HTTPStatus.BAD_REQUEST

        return resp

    def delete(self):
        args = self.parser.parse_args()

        output = self.handler.delete_vpc(args)
        resp = jsonify(output)

        if output["success"] == True:
            resp.status_code = HTTPStatus.OK
        else:
            resp.status_code = HTTPStatus.BAD_REQUEST

        return resp

    def get(self):
        args = request.args  # To get query params in URL

        output = self.handler.get_vpc_by_hosts(args)
        resp = jsonify(output)

        if output["success"] == True:
            resp.status_code = HTTPStatus.OK
        else:
            resp.status_code = HTTPStatus.BAD_REQUEST

        return resp
