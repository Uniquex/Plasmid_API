#!/usr/bin/env python
from MongoCon import MongoCon
from flask_cors import CORS
from influxdb import InfluxDBClient
from werkzeug.security import safe_str_cmp
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
import datetime


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id


users = [
    User(1, 'admin', '123456'),
    User(2, 'user2', 'abcxyz'),
]

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SECRET_KEY'] = 'test-key'
db = MongoCon()
idb = InfluxDBClient('localhost', 8086, 'root', 'root', 'RPI')
jwt = JWTManager(app)


@app.route('/auth', methods=['POST'])
def auth():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username:
        return jsonify({"msg": "Missing username parameter"}), 400
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400

    user = username_table.get(username, None)
    if not user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return jsonify({"msg": "Bad username or password"}), 401

    # Identity can be any data that is json serializable
    expires = datetime.timedelta(days=14)
    access_token = create_access_token(identity=username, expires_delta=expires)
    return jsonify(access_token=access_token), 200


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


@app.route('/server/<servername>', methods=['GET'])
@jwt_required
def server(servername):
    return db.getServer(servername)


@app.route('/server/<servername>/cpuLoad/<time>', methods=['GET'])
@jwt_required
def serverLoadTime(servername, time):
    if time == -1:
        query = 'SELECT CPU_Usage AS "CPU", RAM_Usage AS "RAM"  FROM "RPI"."autogen"."server_load_short" WHERE "host"= \'' + servername + '\' FILL(previous)'
    else:
        query = 'SELECT mean("CPU_Usage") AS "CPU", mean("RAM_Usage") AS "RAM"  FROM "RPI"."autogen"."server_load_short" WHERE "host"= \'' + servername + '\' AND time > now()-' + time + 'h GROUP BY time(5m) FILL(previous)'
    result = idb.query(query)
    return jsonify(result.raw)

@app.route('/server/<servername>/cpuLoad', methods=['GET'])
@jwt_required
def serverLoad(servername):
    query = 'SELECT CPU_Usage AS "CPU", RAM_Usage AS "RAM"  FROM "RPI"."autogen"."server_load_short" WHERE "host"= \'' + servername + '\' FILL(previous)'
    result = idb.query(query)
    return jsonify(result.raw)



@app.route('/servers', methods=['GET'])
@jwt_required
def servers():
    return db.getServers()


@app.route('/cpuLoad', methods=['GET'])
@jwt_required
def cpuLoad():
    result = idb.query('SELECT mean("CPU_Usage") AS "mean_CPU_Usage" FROM "RPI"."autogen"."server_load_short" WHERE "host"=raspberrypi_2 AND time > now()-2h GROUP BY time(5m) FILL(previous)')
    return result.raw


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
