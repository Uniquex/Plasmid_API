#!/usr/bin/env python
from flask import Flask
from flask_restful import Api, Resource, reqparse
from MongoCon import MongoCon
from flask_cors import CORS


app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
api = Api(app)
db = MongoCon()


class Server(Resource):

    def get(self, servername):
        return db.getServer(servername)
        pass


class Test(Resource):

    def get(self):
        return {"test": 3023, "xy": "xykd"}


if __name__ == '__main__':
    api.add_resource(Server, "/server/<servername>")
    api.add_resource(Test, "/test")

    app.run(host='0.0.0.0',debug=True)