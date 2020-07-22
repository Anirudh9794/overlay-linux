from flask import jsonify, Response, request
from flask_restful import Resource, reqparse, abort
from overlay_logic.transit_handler import TransitHandler
from http import HTTPStatus


class Transit_Controller(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('customerId')
        self.parser.add_argument('host')
        self.parser.add_argument('reliabilityFactor')  # must be an integer

        self.handler = TransitHandler()

    def post(self):
        args = self.parser.parse_args()
        output = self.handler.create_transit(args)
        resp = jsonify(output)
        return resp

    def delete(self):
        args = self.parser.parse_args()
        output = self.handler.delete_transit(args)
        resp = jsonify(output)
        return resp

    def get(self):
        args = request.args  # To get query params in URL
        output = self.handler.get_transit(args)
        resp = jsonify(output)
        return resp
