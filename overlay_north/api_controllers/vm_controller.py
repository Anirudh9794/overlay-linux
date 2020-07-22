import sys
from flask import jsonify, Response
from flask_restful import Resource, reqparse, abort
from overlay_logic.vm_handler import VMHandler
from http import HTTPStatus


class VM_Controller(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('customerId')
        self.parser.add_argument('vpcId')
        self.parser.add_argument('subnetId')
        self.parser.add_argument('vmName')

        self.handler = VMHandler()

    def post(self):
        args = self.parser.parse_args()

        output = self.handler.create_vm(args)
        resp = jsonify(output)

        if output["success"] == False:
            resp.status_code = HTTPStatus.BAD_REQUEST
        else:
            resp.status_code = HTTPStatus.CREATED

        return resp

    def delete(self):
        args = self.parser.parse_args()

        output = self.handler.delete_vm(args)
        resp = jsonify(output)

        if output["success"] == False:
            resp.status_code = HTTPStatus.BAD_REQUEST
        else:
            resp.status_code = HTTPStatus.OK

        return resp
