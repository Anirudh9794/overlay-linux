import sys
from flask import jsonify, Response
from flask_restful import Resource, reqparse, abort
from overlay_logic.config_handler import ConfigHandler
from http import HTTPStatus


class Config_Controller(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('cleanStart', required=True)

        self.handler = ConfigHandler()

    def post(self):
        args = self.parser.parse_args()

        output = {}

        if args["cleanStart"] == True:
            output = self.handler.clean_start()

        resp = jsonify(output)

        if output["success"] == False:
            resp.status_code = HTTPStatus.BAD_REQUEST
        else:
            resp.status_code = HTTPStatus.OK

        return resp
