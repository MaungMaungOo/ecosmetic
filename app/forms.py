from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, IntegerField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileField, FileRequired, FileAllowed
from enum import Enum

class Category(Enum):
    Skincare_Products = 'Skincare Products'
    Makeups = 'Makeups'
    Lipsticks = 'Lipsticks'
    Others = 'Others'

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddProductsForm(FlaskForm):
    productname = StringField('Product Name', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired(), NumberRange(min = 1)])
    detail_information = TextAreaField('Detail Information', validators=[DataRequired()])
    category = SelectField('Category', choices=[(member.value, member.value) for name, member in Category.__members__.items()])
    photo = FileField('Photos', validators=[FileRequired('File was empty!')])
    profile_photo = FileField('Profile Photo', validators=[FileRequired('File was empty!')])
    submit = SubmitField('Add Product')

class AddToCartForm(FlaskForm):
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min = 1)])
    loveit = BooleanField('Love It', validators=[DataRequired()])