import os, json
from flask import render_template, flash, request, redirect, url_for, session
from app import app, db
from app.forms import LoginForm, AddProductsForm, AddToCartForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Products
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse
from time import gmtime, strftime
from flask_paginate import Pagination, get_page_args

@app.route('/')
@app.route('/index')
def index():
    form = AddToCartForm()
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
    per_page = app.config["PRODUCTS_PER_PAGE"]
    products = Products.query.all()
    total = len(products)
    offset = (page - 1) * per_page
    pagination_products = products[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap4')
    return render_template('index.html', title='Home', products=pagination_products, page=page,
                           per_page=per_page, pagination=pagination, form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first_or_404()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = AddProductsForm()
    if form.validate_on_submit():
        image_folder = strftime("%Y-%m-%d-%H-%M-%S", gmtime())
        if 'photo' not in request.files:
            return redirect(url_for('add_product'))
        photos = request.files.getlist('photo')
        profile_photo = request.files['profile_photo']
        if not os.path.exists(app.config['UPLOAD_FOLDER']+'\\'+image_folder):
            os.makedirs(app.config['UPLOAD_FOLDER']+'\\'+image_folder)
        else:
            return redirect(url_for('add_product'))
        count = 2;
        for photo in photos:
            if photo.filename == '':
                flash('No selected image')
                return redirect(url_for('add_product'))
            if photo and allowed_file(photo.filename):
                filename = secure_filename(str(count)+'.'+photo.filename.rsplit('.', 1)[1].lower())
                count += 1;
                photo.save(os.path.join(app.config['UPLOAD_FOLDER']+'\\'+image_folder, filename))
        profile_photo_filename = secure_filename('1.'+profile_photo.filename.rsplit('.', 1)[1].lower())
        profile_photo.save(os.path.join(app.config['UPLOAD_FOLDER']+'\\'+image_folder, profile_photo_filename))
        profile_location = image_folder+'/'+profile_photo_filename
        product = Products(product_name=form.productname.data, price=form.price.data,
                            detail_information=form.detail_information.data, category=form.category.data,
                            photo = image_folder, profile_photo = profile_location)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('add_product'))
    return render_template('add_product.html', title='Add Product', form=form)

# @app.route('/delete_product')

@app.route('/view_products')
def view_products():
    form = AddToCartForm()
    products = Products.query.all()
    return render_template('view_products.html', form=form, products=products, title='View Products')

@app.route('/product_detail/<int:id>')
def product_detail(id):
    form = AddToCartForm()
    product = Products.query.filter_by(id=id).first_or_404()
    img_url = os.path.abspath(os.path.join(app.config["UPLOAD_FOLDER"],product.photo))
    image_list = [f for f in os.listdir(img_url) if os.path.isfile(os.path.join(img_url, f))]
    return render_template('product_detail.html', form=form, product=product, image_list=image_list, title='Product Detail')

@app.route('/add_to_cart', methods=['GET', 'POST'])
def add_to_cart():
    if request.method == 'POST':
        quantity = request.form.get("quantity")
        id = request.form.get("id")
        checkbox = request.form.get("checkbox")
    else:
        return json.dumps()

    if "cart" not in session:
        session["cart"] = []
    session.modified = True
    found = False
    for item in session['cart']:
        if item['id']==id:
            item["quantity"]=int(item["quantity"])+int(quantity)
            found = True
    if not found:
        product = {}
        product.update( {'id' : id} )
        product.update( {'quantity' : quantity} )
        session["cart"].append(product)

    if "total" not in session:
        session["total"] = 0
    session["total"] += int(quantity)

    if checkbox=="checked":
        product = Products.query.filter_by(id=id).first_or_404()
        product.popular += 1;
        db.session.commit()

    return json.dumps({"total":session["total"]})

@app.route('/remove_cart_item', methods=['DELETE'])
def remove_cart_item():
    if request.method == 'DELETE':
        id = request.form.get("id")
        quantity = request.form.get("quantity")
    else:
        return json.dumps()
    
    session.modified = True
    for item in session['cart']:
        if item['id']==id:
            session['cart'].remove(item)
    session["total"] = int(session["total"]) - int(quantity)
    return json.dumps({"total":session["total"]})

@app.route('/cart')
def cart():
    if "cart" not in session:
        session["cart"] = []
    items = session["cart"]
    dict_of_products = {}
    total_price = 0

    for item in items:
        product = Products.query.filter_by(id=item['id']).first_or_404()
        total_price += product.price
        if product.id in dict_of_products.keys():
            dict_of_products[product.id]["quantity"] += int(item['quantity'])
        else:
            dict_of_products[product.id] = {"quantity":int(item['quantity']), 
                                            "name": product.product_name, 
                                            "price":int(product.price),
                                            "image":product.profile_photo}

    return render_template("cart.html", display_cart = dict_of_products, total = total_price)