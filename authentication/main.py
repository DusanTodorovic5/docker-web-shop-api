import re

from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, User, Role
from email.utils import parseaddr
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity, verify_jwt_in_request
from sqlalchemy import and_
from functools import wraps

application = Flask(__name__)
application.config.from_object(Configuration)
# testing
# python main.py --type authentication --authentication-address http://127.0.0.1:5000 --jwt-secret JWTSecretDevKey --roles-field roles --administrator-role 1 --customer-role 2 --warehouse-role 3

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)


def has_upper(inputString):
    return any(char.isupper() for char in inputString)


def has_lower(inputString):
    return any(char.islower() for char in inputString)


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
                    "msg":"Missing Authorization Header"
                }), 401
        return decorator
    return innerRole

@application.route("/", methods=["GET"])
def index():
    return "radim"

@application.route("/register", methods=["POST"])
def register():
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    role = request.json.get("isCustomer", None)

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0

    if forenameEmpty:
        return jsonify({
            "message": "Field forename is missing."
        }), 400

    if surnameEmpty:
        return jsonify({
            "message": "Field surname is missing."
        }), 400

    if emailEmpty:
        return jsonify({
            "message": "Field email is missing."
        }), 400

    if passwordEmpty:
        return jsonify({
            "message": "Field password is missing."
        }), 400

    if role == None:
        return jsonify({
            "message": "Field isCustomer is missing."
        }), 400

    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if not re.search(regex,email):
        return jsonify({
            "message": "Invalid email."
        }), 400

    if len(password) < 8 or not has_numbers(password) or not has_upper(password) or not has_lower(password):
        return jsonify({
            "message": "Invalid password."
        }), 400

    myRole = 2
    if role:
        myRole = 2
    else:
        myRole = 3

    #exists = (User.query.filter(User.email == email).first())

    if User.query.filter(User.email == email).first():
        return jsonify({
            "message": "Email already exists."
        }), 400

    user = User(email=email, password=password, forename=forename, surname=surname, role=myRole)
    database.session.add(user)
    database.session.commit()

    return Response(status=200)


jwt = JWTManager(application)


@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    if emailEmpty:
        return jsonify({
            "message": "Field email is missing."
        }), 400

    if passwordEmpty:
        return jsonify({
            "message": "Field password is missing."
        }), 400

    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if not re.search(regex, email):
        return jsonify({
            "message": "Invalid email."
        }), 400

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if not user:
        return jsonify({
            "message": "Invalid credentials."
        }), 400

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "email": user.email,
        "roles": str(user.role)
    }


    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)

    return jsonify(accessToken=accessToken, refreshToken=refreshToken)


@application.route("/check", methods=["POST"])
@jwt_required()
def check():
    return "Token is valid!";


@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additionalClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "email": refreshClaims["email"],
        "roles": refreshClaims["roles"]
    }

    return jsonify(accessToken=create_access_token(identity=identity, additional_claims=additionalClaims)), 200


@application.route("/delete", methods=["POST"])
@roleCheck(role="1")
def delete():
    email = request.json.get("email", "")

    emailEmpty = len(email) == 0

    if emailEmpty:
        return jsonify({
            "message": "Field email is missing."
        }), 400

    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if not re.search(regex, email):
        return jsonify({
            "message": "Invalid email."
        }), 400

    user = User.query.filter(User.email == email).first()
    if user:
        User.query.filter(User.email == email).delete()
        database.session.commit()

        return Response(status=200)

    return jsonify({
                "message": "Unknown user."
            }), 400


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5000)
