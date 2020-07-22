from flask import jsonify, Response, request
from flask_restful import Resource, reqparse, abort
from overlay_logic.tunnel_handler import TunnelHandler
from http import HTTPStatus


class Tunnel_Controller(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('customerId')
        self.parser.add_argument('vpcId')
        self.parser.add_argument('transitId')
        self.parser.add_argument('tunnelId')
        self.parser.add_argument('tunnelType')  # "l2" or "l3"

        self.handler = TunnelHandler()

    def post(self):
        args = self.parser.parse_args()

        output = self.handler.create_tunnel(args)
        resp = jsonify(output)

        return resp

    def delete(self):
        args = self.parser.parse_args()
        output = self.handler.delete_tunnel(args)
        resp = jsonify(output)
        return resp
