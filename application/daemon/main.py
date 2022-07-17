from flask import Flask
from configuration import Configuration
from models import database, Product, ProductCategories, Category, ProductOrders, Order
import redis

if __name__ == "__main__":
    application = Flask(__name__)
    application.config.from_object(Configuration)
    database.init_app(application)
    red = redis.StrictRedis(host=Configuration.REDIS_HOST, charset="utf-8", decode_responses=True)
    pubsub = red.pubsub()
    pubsub.subscribe("storekeeper")

    while True:
        for msg in pubsub.listen():
            with application.app_context() as context:
                row = msg['data']
                if not type(row) == str:
                    continue
                row = row.split(",")
                categories = row[0].split('|')
                name = row[1]
                quantity = int(row[2])
                price = float(row[3])
                product = Product.query.filter(Product.name == row[1]).first()
                if product:
                    good = True
                    for category in categories:
                        if not any(cat.name == category for cat in product.categories):
                            good = False
                            break
                    if not good:
                        continue
                    new_price = (product.number * product.cost + quantity * price) / float(product.number + quantity)
                    product.cost = new_price
                    product.number = product.number + quantity
                    database.session.commit()
                else:
                    product = Product(name=name, cost=price, number=quantity)
                    for category in categories:
                        old_category = Category.query.filter(Category.name == category).first()
                        if not old_category:
                            new_category = Category(name=category)
                            database.session.add(new_category)
                            database.session.commit()
                    database.session.add(product)
                    database.session.commit()
                    product = Product.query.filter(Product.name == row[1]).first()
                    for category in categories:
                        cat = Category.query.filter(Category.name == category).first()
                        pc = ProductCategories(productId=product.id, categoryId=cat.id)
                        database.session.add(pc)
                        database.session.commit()
                orders = Order.query.filter(Order.status == "PENDING").join(ProductOrders).join(Product).filter(
                    Product.name == product.name).group_by(Order.id).all()

                for order in orders:
                    orderedProds = ProductOrders.query.filter(ProductOrders.orderId == order.id)

                    for ord_prod in orderedProds:
                        if ord_prod.productId != product.id or ord_prod.requested == ord_prod.received or product.number == 0:
                            continue

                        if product.number > ord_prod.requested - ord_prod.received:
                            product.number -= (ord_prod.requested - ord_prod.received)
                            ord_prod.received = ord_prod.requested
                            database.session.commit()
                        else:
                            ord_prod.received += product.number
                            product.number = 0
                            database.session.commit()
                            break

                    leftRequests = ProductOrders.query.filter(ProductOrders.orderId == order.id)

                    found = False
                    for req in leftRequests:
                        if req.requested != req.received:
                            found = True
                            break

                    if not found:
                        order.status = "COMPLETE"
                        database.session.commit()