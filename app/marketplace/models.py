# app/marketplace/models.py
import uuid
from datetime import datetime
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from scripts.utils import utcnow


class Seller(db.Model):
    __tablename__ = 'market_seller'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: uuid.uuid4().hex)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    ads = db.relationship('Advertisement', backref='seller', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Advertisement(db.Model):
    __tablename__ = 'market_advertisement'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: uuid.uuid4().hex)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)

    seller_id = db.Column(db.Integer, db.ForeignKey('market_seller.id'), nullable=False)
    products = db.relationship('Product', backref='advertisement', cascade='all, delete-orphan')


class Product(db.Model):
    __tablename__ = 'market_product'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: uuid.uuid4().hex)
    ad_id = db.Column(db.Integer, db.ForeignKey('market_advertisement.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price_inr = db.Column(db.Float, nullable=False)
    is_sold = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(500), nullable=True)  # Optional image URL

    bookings = db.relationship('ProductBooking', backref='product', cascade='all, delete-orphan')


class ProductBooking(db.Model):
    __tablename__ = 'market_booking'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('market_product.id'), nullable=False)
    buyer_email = db.Column(db.String(255), nullable=False)
    otp_code = db.Column(db.String(10))
    is_verified = db.Column(db.Boolean, default=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
