from flask import Flask, Response, jsonify
from sqlalchemy import func

from configuration import Configuration
from models import database, ProductOrders, Product, Category, ProductCategories
from flask_jwt_extended import JWTManager, get_jwt, verify_jwt_in_request
from functools import wraps

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


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


@application.route("/productStatistics", methods=["GET"])
@roleCheck(role="1")
def productStatistics():
    products = Product.query.all()
    statistic = []

    for product in products:
        orders = ProductOrders.query.filter(ProductOrders.productId == product.id).all()
        sold = 0
        waiting = 0
        for order in orders:
            sold = sold + order.requested
            waiting = waiting + order.requested - order.received
        if sold + waiting != 0:
            statistic.append({
                "name": product.name,
                "sold": sold,
                "waiting": waiting
            })

    return jsonify({
        "statistics": statistic
    })


@application.route("/categoryStatistics", methods=["GET"])
@roleCheck(role="1")
def categoryStatistics():
    statistics = []

    categories = Category.query.outerjoin(ProductCategories).outerjoin(Product)\
        .outerjoin(ProductOrders).group_by(Category.id)\
        .order_by(func.sum(ProductOrders.requested).desc()).order_by(Category.name)

    for category in categories:
        statistics.append(category.name)

    return jsonify({
        "statistics": statistics
    })

if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5003)
