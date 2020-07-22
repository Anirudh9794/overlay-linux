import sys
from flask import jsonify, Response
from flask_restful import Resource, reqparse, abort
from overlay_logic.customer_handler import CustomerHandler
from http import HTTPStatus


class Customer_Controller(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('customerName')

        self.handler = CustomerHandler()

    def post(self):
        args = self.parser.parse_args()
        print(args)
        if not args['customerName']:
            print('no customer name')
            return

        output = self.handler.create_customer(args)
        resp = jsonify(output)

        if output["success"] == True:
            resp.status_code = HTTPStatus.CREATED
        else:
            resp.status_code = HTTPStatus.BAD_REQUEST

        return resp

    def get(self):
        output = self.handler.get_all_customers()
        resp = jsonify(output)
        return resp

    def delete(self):
        args = self.parser.parse_args()
        print(args)
        output = {}
        if not args['customerName']:
            output["message"] = "No customer name provided"
            return output

        output = self.handler.delete_customer(args)
        resp = jsonify(output)

        if output["success"] == True:
            resp.status_code = HTTPStatus.OK
        else:
            resp.status_code = HTTPStatus.BAD_REQUEST

        return resp
