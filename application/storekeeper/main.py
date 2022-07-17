import csv
import io

from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database
from flask_jwt_extended import JWTManager, get_jwt, verify_jwt_in_request
from functools import wraps
from redis import Redis

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)

def is_correct(str):
    try:
        float(str)
    except ValueError:
        return False
    return float(str) > 0


def roleCheck(role):
    def innerRole(function):
        @wraps(function)
        def decorator(*arguments, **keywordArguments):
            verify_jwt_in_request()
            claims = get_jwt()
            if role == claims["roles"]:
                return function(*arguments, **keywordArguments)
            else:
                return jsonify({
                    "msg": "Missing Authorization Header"
                }), 401

        return decorator

    return innerRole


@application.route("/update", methods=["POST"])
@roleCheck(role="3")
def update():
    if not request.files.get("file", None):
        return jsonify({
            "message": "Field file is missing."
        }), 400

    content = request.files["file"].stream.read().decode ("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)
    redis = Redis(host=Configuration.REDIS_HOST)

    products = []
    i = 0
    for row in reader:
        if len(row) != 4:
            return jsonify({
                "message": "Incorrect number of values on line {}.".format(i)
            }), 400
        if not is_correct(row[2]):
            return jsonify({
                "message": "Incorrect quantity on line {}.".format(i)
            }), 400
        if not is_correct(row[3]):
            return jsonify({
                "message": "Incorrect price on line {}.".format(i)
            }), 400
        line = "{},{},{},{}".format(row[0], row[1], row[2], row[3])
        products.append(line)
        i = i + 1

    with Redis(host=Configuration.REDIS_HOST) as redis:
        for row in products:
            redis.publish(channel="storekeeper", message=row)

    return Response(status=200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)
