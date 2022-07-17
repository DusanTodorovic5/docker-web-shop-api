from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, Category, ProductCategories, Product, Order, ProductOrders
from flask_jwt_extended import JWTManager, get_jwt, verify_jwt_in_request
from sqlalchemy import and_
from functools import wraps
from datetime import datetime

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

@application.route("/search", methods=["GET"])
@roleCheck(role="2")
def search():
    name = request.args.get("name", None)
    category = request.args.get("category", None)

    categories = []
    products = []

    if category and name:
        categories = Category.query.join(ProductCategories).join(Product).filter(
            and_(
                *[
                    Category.name.like(f"%{category}%"),
                    Product.name.like(f"%{name}%")
                ]
            )
        ).group_by(Category.id).with_entities(Category.name).all()
        products = Product.query.join(ProductCategories).join(Category).filter(
            and_(
                *[
                    Product.name.like(f"%{name}%"),
                    Category.name.like(f"%{category}%")
                ]
            )
        ).group_by(Product.id).all()
    elif category:
        categories = Category.query.join(ProductCategories).join(Product).filter(
            and_(
                *[
                    Category.name.like(f"%{category}%")
                ]
            )
        ).group_by(Category.id).with_entities(Category.name).all()
        products = Product.query.join(ProductCategories).join(Category).filter(
            and_(
                *[
                    Category.name.like(f"%{category}%")
                ]
            )
        ).group_by(Product.id).all()
    elif name:
        categories = Category.query.join(ProductCategories).join(Product).filter(
            and_(
                *[
                    Product.name.like(f"%{name}%")
                ]
            )
        ).group_by(Category.id).with_entities(Category.name).all()
        products = Product.query.join(ProductCategories).join(Category).filter(
            and_(
                *[
                    Product.name.like(f"%{name}%")
                ]
            )
        ).group_by(Product.id).all()
    else:
        categories = Category.query.with_entities(Category.name).all()
        products = Product.query.all()

    json_category = []
    for cat in categories:
        json_category.append(cat[0])
    json_product = []
    for product in products:
        product_categories = []
        for product_cat in product.categories:
            product_categories.append(product_cat.name)
        json_product.append({
            "categories": product_categories,
            "id": product.id,
            "name": product.name,
            "price": product.cost,
            "quantity": product.number
        })

    final_json = {
        "categories": json_category,
        "products": json_product
    }
    return jsonify(final_json)

@application.route("/order", methods=["POST"])
@roleCheck(role="2")
def order():
    requests = request.json.get("requests", "")

    if len(requests) == 0:
        return jsonify({
            "message": "Field requests is missing."
        }), 400

    i = 0
    for req in requests:
        if req.get("id", "") == "":
            return jsonify({
                "message": "Product id is missing for request number {}.".format(i)
            }), 400
        if req.get("quantity", "") == "":
            return jsonify({
                "message": "Product quantity is missing for request number {}.".format(i)
            }), 400
        flag = True
        try:
            t = int(req['id'])
        except ValueError:
            return jsonify({
                "message": "Invalid product id for request number {}.".format(i)
            }), 400
        if int(req["id"]) <= 0:
            return jsonify({
                "message": "Invalid product id for request number {}.".format(i)
            }), 400
        try:
            t = int(req['quantity'])
        except ValueError:
            return jsonify({
                "message": "Invalid product quantity for request number {}.".format(i)
            }), 400
        if int(req['quantity']) <= 0:
            return jsonify({
                "message": "Invalid product quantity for request number {}.".format(i)
            }), 400
        product = Product.query.filter(Product.id == req['id']).first()
        if product is None:
            return jsonify({
                "message": "Invalid product for request number {}.".format(i)
            }), 400
        i = i + 1

    order = Order(cost=0, status="PENDING", date=datetime.today(), user_id=1)
    database.session.add(order)
    database.session.commit()

    cost = 0
    notFullfilled = False

    for req in requests:
        product = Product.query.filter(Product.id == req['id']).first()
        cost = float(cost) + float(product.cost) * float(req['quantity'])
        po = ProductOrders(productId=req["id"], orderId=order.id, cost=product.cost, received=0, requested=req["quantity"])

        if product.number >= req['quantity']:
            product.number = product.number - req["quantity"]
            po.received = req["quantity"]
        else:
            notFullfilled = True
            po.received = product.number
            product.number = 0

        database.session.add(po)
        database.session.commit()

    if not notFullfilled:
        order.status = "COMPLETE"
    order.cost = cost
    database.session.commit()

    return jsonify({
        "id":order.id
    })

@application.route("/status", methods=["GET"])
@roleCheck(role="2")
def status():
    user = 1

    orders = Order.query.filter(Order.user_id == user).all()

    my_orders = []

    for order in orders:
        orderProducts = ProductOrders.query.filter(ProductOrders.orderId == order.id).all()
        products = []
        for orderProduct in orderProducts:
            name = Product.query.filter(Product.id == orderProduct.productId).first().name
            queryCategories = ProductCategories.query.filter(ProductCategories.productId == orderProduct.productId).all()
            categories = []
            for cat in queryCategories:
                category = Category.query.filter(Category.id == cat.categoryId).first()
                categories.append(category.name)
            products.append({
                "categories": categories,
                "name": name,
                "price": orderProduct.cost,
                "received": orderProduct.received,
                "requested": orderProduct.requested
            })
        my_orders.append({
            "products": products,
            "price": order.cost,
            "status": order.status,
            "timestamp": order.date
        })

    return jsonify({
        "orders": my_orders
    })


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5001)
