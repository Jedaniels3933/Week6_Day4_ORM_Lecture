from flask import Flask, jsonify, request
# Flask class - gives us all the tools we need to create a Flask application (web application) by creating an instance of the Flask class
# jsonify - Converts data into JSON format
# requests - allows us to interact with HTTP method requests as objects
from flask_sqlalchemy import SQLAlchemy
# SQLALchemy - ORM to connect and relate Python classes to database tables
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
# DeclarativeBase - gives us the base model functionality to create classes as models for our database tables, also track the metadata for our tables and classes
# Mapped - Maps a class attribute to a table column (or relationship)
# mapped_column - sets our columns and allows us to add any constraints we might need (unique, nullable, primary_key)
from flask_marshmallow import Marshmallow
# Marshmallow - allows us to create schema to validate, serialize, and deserialize JSON data
from datetime import date
# datetime - allows us to create datetime objects
from typing import List
# List - is used to create a relationship that will return a list of objects
from marshmallow import ValidationError, fields
# fields - lets us set a schema field which includes data types and constraints
from sqlalchemy import select, delete
# select - acts as our SELECT FROM query
# delete - act as our DELETE query


app = Flask(__name__) # creating an instance of the Flask class for our app to use

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:%21%3F12ABpp@localhost/ecom'

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class= Base)
ma = Marshmallow(app)

#================= Models (tables as classes) (using SQLAlchemy) =================#

class Customer(Base):
    __tablename__ = "customer" # make you class name the same as your table name, and the table name should be exactly as it is in your database

    # Mapping our class attribute to our table columns
    id: Mapped[int] = mapped_column(primary_key= True)
    customer_name: Mapped[str] = mapped_column(db.String(75), nullable= False)
    email: Mapped[str] = mapped_column(db.String(150))
    phone: Mapped[str] = mapped_column(db.String(16))
    address: Mapped[str] = mapped_column(db.String(150) , nullable = True)
    # Create a one-many relationship to Orders table
    orders: Mapped[List["Orders"]] = db.relationship(back_populates= 'customer') # back populates ensures that both ends of this relationship have access to this information

order_products = db.Table(
    "order_products",
    Base.metadata, # allows this table to locate foreign keys from the Base class
    db.Column('order_id', db.ForeignKey('orders.id'), primary_key= True),
    db.Column('product_id', db.ForeignKey('products.id'), primary_key= True)
)


class Orders(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key= True)
    order_date: Mapped[date] = mapped_column(db.Date, nullable= False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customer.id'))

    # create a many-one relationship to the Customer table
    customer: Mapped['Customer'] = db.relationship(back_populates= 'orders')

    # create a many-many relationship to Products through an association table order_products
    products: Mapped[List['Products']] = db.relationship(secondary= order_products)


class Products(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key= True)
    product_name: Mapped[str] = mapped_column(db.String(255), nullable= False)
    price: Mapped[float] = mapped_column(db.Float, nullable= False)

with app.app_context():
    #db.drop_all() #drops all tables in database
    db.create_all() # creates all tables in database, first checks to see if table exists , and then creates the tabes if they do not exist, if table with same name found , does not reconstruct it 

# Marshmallow Schema Data Validation

#Define Schema for Customer to check if data is valid

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    id = fields.Integer(required = False)   # required = False means that this field is not required
    customer_name = fields.String(required = True) # required = True means that this field is required
    email = fields.String()
    phone = fields.String() 

    class Meta:
        fields = ('id', 'customer_name', 'email', 'phone')
        
class OrdersSchema(ma.SQLAlchemyAutoSchema):
    id = fields.Integer(required = False)
    order_date = fields.Date(required = True)
    customer_id = fields.Integer(required = True)

    class Meta:
        fields = ('id', 'order_date', 'customer_id', 'items') # items will be a list of products id's associated with an order

class ProductsSchema(ma.SQLAlchemyAutoSchema):
    id = fields.Integer(required = False)
    product_name = fields.String(required = True)
    price = fields.Float(required = True)

    class Meta:
        fields = ('id', 'product_name', 'price')

#Instances of the schema classes

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many = True)

order_schema = OrdersSchema()
orders_schema = OrdersSchema(many = True)

product_schema = ProductsSchema()
products_schema = ProductsSchema(many = True)


#================= Routes =================#
@app.route('/')
def home():
    return "Welcome to the E-commerce API"

#CRUD OPs

# Create is POST
#Retrieve is GET
#Update is PUT
#Delete is DELETE

#================= Customer Routes =================#

#Get all customers

@app.route("/customers", methods = ["GET"])

def get_customers():
    query= select(Customer)  # Select all FROM Customer 
    result = db.session.execute(query).scalars() # Execute and convert into a scaler object or python useable 
    customers= result.all()
    return customers_schema.jsonify(customers)

#Get a single customer

@app.route("/customers/<int:id>", methods = ["GET"])

def get_customer(id):
    query = select(Customer).where(Customer.id == id)
    result = db.session.execute(query).scalers().first()  #first used to get the first object in the list

    if result is None:
        return jsonify({"Error": "Customer not found"}), 404
    return customer_schema.jsonify(result)

#Create a customer with a POST request 

@app.route("/customers", methods = ["POST"])

def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_customer = Customer(customer_name = customer_data['customer_name'], email = customer_data['email'], phone = customer_data['phone'])
    db.session.add(new_customer)    #add the new customer to the session
    db.session.commit()
    return jsonify({"message": "Customer added successfully"}), 201
    
#Update customer with a Put request 
@app.route("/customers/<int:id>", methods = ["PUT"])
def update_customer(id):
    query = select(Customer).where(Customer.id == id)
    result = db.session.execute(query).scalars()

    if result is None:
        return jsonify({"Error": "Customer not found"}), 404

    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify({"error""message"}), 400

    customer = result
    try:
        customer_date = customer_schema.load
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    for field,value in customer_data.items():
        setattr(customer, field, value)
    db.session.commit()
    return jsonify({"message": "Customer updated successfully"}), 200

#Delete a customer with a DELETE request

@app.route("/customers/<int:id>", methods = ["DELETE"])
def delete_customer(id):
    query = delete(Customer).where(Customer.id == id)  #delete FROM  Customer WHERE id = id
    result = db.session.execute(query)

    if result.rowcount == 0 :
        return jsonify({"Error": "Customer not found"}), 404

    db.session.commit()
    return jsonify({"message": "Customer deleted successfully"}), 200

#============= Product Interactions =================#

# Route to create/add new products with a POST request
@app.route("/products", methods=['POST'])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Products(product_name = product_data['product_name'], price = product_data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "Product added successfully"}), 201


@app.route("/products", methods=['GET'])
def get_products():
    query = select(Products)
    result = db.session.execute(query).scalars()

    products = result.all()

    return products_schema.jsonify(products)

#============= Order Interactions ===============#

# Create/place a new order with a POST request
@app.route("/orders", methods=['POST'])
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    new_order = Orders(order_date = date.today(), customer_id = order_data['customer_id'])

    for item_id in order_data['items']:
        query = select(Products).where(Products.id == item_id)
        item = db.session.execute(query).scalar()
        new_order.products.append(item)

    db.session.add(new_order)
    db.session.commit()
    return jsonify({"Message": "New order placed!"}), 201

# Get items in an order by order ID
@app.route("/order_items/<int:id>", methods = ['GET'])
def order_items(id):
    query = select(Orders).where(Orders.id == id)     
    order = db.session.execute(query).scalar()

    return products_schema.jsonify(order.products)
   
# need to figure out how to use postman to test the routes
# need to figure out how to create a new order with a POST request

if __name__ == '__main__':
    app.run(debug = True)


