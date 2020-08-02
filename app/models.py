from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)  

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return Users.query.get(int(id)) 

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(64), index=True)
    price = db.Column(db.Integer)
    detail_information = db.Column(db.String(512))
    category = db.Column(db.Enum('Skincare Products', 'Makeups', 'Lipsticks', 'Others', name='Category'))
    photo = db.Column(db.String(64), unique=True)
    profile_photo = db.Column(db.String(64), unique=True)
    popular = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Products {}>'.format(self.product_name)  