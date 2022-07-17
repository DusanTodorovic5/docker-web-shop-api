from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class ProductCategories(database.Model):
    __tablename__ = "product_categories"
    id = database.Column(database.Integer, primary_key = True)
    productId = database.Column(database.Integer, database.ForeignKey("products.id"), nullable = False)
    categoryId = database.Column(database.Integer, database.ForeignKey("categories.id"), nullable = False)

    def __repr__(self):
        return "({}, {}, {})".format(self.id, self.productId, self.categoryId)


class ProductOrders(database.Model):
    __tablename__ = "product_orders"
    id = database.Column(database.Integer, primary_key = True)
    productId = database.Column(database.Integer, database.ForeignKey("products.id"), nullable = False)
    orderId = database.Column(database.Integer, database.ForeignKey("orders.id"), nullable = False)
    cost = database.Column(database.Float, nullable = False)
    received = database.Column(database.Integer, nullable = False)
    requested = database.Column(database.Integer, nullable=False)

    def __repr__(self):
        return "({}, {}, {})".format(self.id, self.productId, self.orderId)


class Product(database.Model):
    __tablename__  = "products"
    id = database.Column(database.Integer, primary_key = True)
    name = database.Column(database.String(256), nullable = False)

    cost = database.Column(database.Float, nullable = False)
    number = database.Column(database.Integer, nullable = False)

    categories = database.relationship("Category", secondary=ProductCategories.__table__, back_populates="products")
    orders = database.relationship("Order", secondary=ProductOrders.__table__, back_populates="products")

    def __repr__(self):
        return "({}, {}, {}, {})".format(self.id, self.name, self.cost, self.number)


class Category(database.Model):
    __tablename__ = "categories"
    id = database.Column(database.Integer, primary_key = True)
    name = database.Column(database.String(256), nullable = False)

    products = database.relationship("Product", secondary=ProductCategories.__table__, back_populates="categories")

    def __repr__(self):
        return "({}, {})".format(self.id, self.name)


class Order(database.Model):
    __tablename__ = "orders"
    id = database.Column(database.Integer, primary_key = True)
    cost = database.Column(database.Float, nullable = False)
    status = database.Column(database.String(256), nullable = False)
    date = database.Column(database.DateTime, nullable = False)
    user_id = database.Column(database.Integer, nullable = False)

    products = database.relationship("Product", secondary=ProductOrders.__table__, back_populates="orders")

    def __repr__(self):
        return "({}, {}, {}, {})".format(self.id, self.cost, self.status, self.date)