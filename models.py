import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar = db.Column(db.String(128), default='default_avatar.png') # Store filename

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(10), index=True, unique=True, nullable=False) # NMCF + 4 chars = 8, let's use 10 just in case
    supplier_name = db.Column(db.String(128)) # Added as requested
    customer_name = db.Column(db.String(64), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    issue_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow) # Default to upload time if Excel data is bad
    phone = db.Column(db.String(20), nullable=False)
    coupon_code = db.Column(db.String(15), unique=True, nullable=False) # CX + 7 chars = 9, use 15 for safety
    validity_months = db.Column(db.Integer, nullable=False, default=12)
    status = db.Column(db.String(20), nullable=False, default='已激活') # Default status
    upload_timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Order {self.order_id} for {self.customer_name}>'

    # --- Masking properties for display ---
    @property
    def masked_phone(self):
        if self.phone and len(self.phone) >= 11:
            return f"{self.phone[:3]}****{self.phone[-4:]}"
        return self.phone # Return original if too short

    @property
    def masked_coupon_code(self):
        if self.coupon_code and len(self.coupon_code) >= 9: # CX + 7 = 9
             # Show first 5 chars (CX + 3 random), then 4 stars
            return f"{self.coupon_code[:5]}****"
        return self.coupon_code # Return original if too short