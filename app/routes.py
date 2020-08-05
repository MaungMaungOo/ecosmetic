import os, json, shutil
from flask import render_template, flash, request, redirect, url_for, session, abort, send_file
from app import app, db
from app.forms import LoginForm, AddProductsForm, AddToCartForm, OrderForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import Users, Products
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse
from time import gmtime, strftime
from flask_paginate import Pagination, get_page_args
#libraries to create the pdf file and add text to it
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
#library to get logo related information
from PIL import Image
#get today date
from datetime import date, datetime

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
        user = Users.query.filter_by(username=form.username.data).first_or_404()
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
        if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], image_folder)):
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], image_folder))
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
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], image_folder, filename))
        profile_photo_filename = secure_filename('1.'+profile_photo.filename.rsplit('.', 1)[1].lower())
        profile_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], image_folder, profile_photo_filename))
        profile_location = image_folder+'/'+profile_photo_filename
        product = Products(product_name=form.productname.data, price=form.price.data,
                            detail_information=form.detail_information.data, category=form.category.data,
                            photo = image_folder, profile_photo = profile_location)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('add_product'))
    return render_template('add_product.html', title='Add Product', form=form)

@app.route('/delete_from_db', methods=['DELETE'])
@login_required
def delete_from_db():
    if request.method == 'DELETE':
        id = request.form.get("id")
    else:
        abort(405)
    product = Products.query.filter_by(id=id).first_or_404()
    if product:
        try:
            dir_path = os.path.join(app.config['UPLOAD_FOLDER'], product.photo)
            shutil.rmtree(dir_path)
        except OSError as e:
            print(os.path.join(app.config['UPLOAD_FOLDER'], product.photo))
            abort(Response("Error deleting files!"))
        db.session.delete(product)
        db.session.commit()
        return json.dumps({"success":""})
    else:
        abort(Response("There is no such product!"))

@app.route('/delete_product')
@login_required
def delete_product():
    products = Products.query.all()
    return render_template('delete_product.html', products=products, title='Delete Products')

@app.route('/view_products/<string:category>')
def view_products(category):
    form = AddToCartForm()
    no_product = False
    products = Products.query.filter_by(category=category).all()
    if not products:
        no_product = True
    return render_template('view_products.html', form=form, no_product=no_product, products=products, title='View Products')

@app.route('/product_detail/<int:id>')
def product_detail(id):
    form = AddToCartForm()
    product = Products.query.filter_by(id=id).first_or_404()
    img_url = os.path.join(app.config['UPLOAD_FOLDER'], product.photo)
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
        price = request.form.get("price")
    else:
        return json.dumps()
    
    session.modified = True
    for item in session['cart']:
        if item['id']==id:
            session['cart'].remove(item)

    del session["order"][id]
    
    total = int(quantity) * int(price)
    session["total"] = int(session["total"]) - int(quantity)
    return json.dumps({"total":session["total"],"tprice":total})

@app.route('/cart')
def cart():
    if "cart" not in session:
        session["cart"] = []
    items = session["cart"]
    dict_of_products = {}
    total_price = 0

    for item in items:
        product = Products.query.filter_by(id=item['id']).first_or_404()
        price = product.price * int(item['quantity'])
        total_price += price
        if product.id in dict_of_products.keys():
            dict_of_products[product.id]["quantity"] += int(item['quantity'])
        else:
            dict_of_products[product.id] = {"quantity":int(item['quantity']), 
                                            "name": product.product_name, 
                                            "price":int(product.price),
                                            "image":product.profile_photo}
    form = OrderForm()
    if "order" not in session:
        session["order"] = []
    session.modified = True
    session["order"] = dict_of_products

    return render_template("cart.html", display_cart=dict_of_products, form=form, total=total_price, title='Shopping Cart')

#convert the font so it is compatible
pdfmetrics.registerFont(TTFont('Arial','Arial.ttf'))
#import company's logo
im = Image.open('app/static/images/staticImages/logo.png')
width, height = im.size
ratio = width/height
image_width = 400
image_height = int(image_width / ratio)

#Page information
page_width = 2156
page_height = 3050

#Invoice variables
company_name ='ECOSMETIC'
company_email = 'support@company.com'
phoneno = '09 695 701908'
margin = 100

#def function
def generate_pdf(orders,customer,address,c_phoneno,special_req):
    #Creating a pdf file and setting a naming convention
    now = datetime.now()
    pdf_name = now.strftime("%Y-%m-%d-%H-%M-%S")
    today = date.today()
    month_year = today.strftime("%B %d, %Y")
    invoice_number = now.strftime("%Y%m%d%H%M%S")
    c = canvas.Canvas("app/static/orders/"+pdf_name +'.pdf')
    c.setPageSize((page_width, page_height))

    #Drawing the image
    c.drawImage("app/static/images/staticImages/logo.png", page_width - image_width - margin,
                        page_height - image_height - margin, image_width, image_height, mask="auto")

    #Invoice information
    c.setFont('Arial',80)
    text = 'INVOICE'
    text_width = stringWidth(text,'Arial',80)
    c.drawString((page_width-text_width)/2, page_height - image_height - margin, text)
    y = page_height - image_height - margin*4
    x = 2*margin
    x2 = x + 500
    x3 = x2 + 500
    x4 = x3 + 500
    
    c.setFont('Arial', 45)
    c.drawString(x,y, company_name)
    c.drawString(x3,y,"Purchased Date: "+month_year)
    y -= margin
    
    c.drawString(x,y,company_email)
    c.drawString(x3,y,'Customer Name: '+customer)
    y -= margin

    c.drawString(x,y,phoneno)
    c.drawString(x3,y,'Invoice number: '+str(invoice_number))
    y -= margin

    c.drawString(x,y,"Delivery Address:")
    y -= margin

    if len(address) > 90:
        wrap_text = textwrap.wrap(special_req, width=90)
        for text in wrap_text:
            c.drawString(x, y, text)
            y -= margin
    else:
        c.drawString(x, y, address)
        y -= margin

    c.drawString(x,y,"Customer Contact:")
    y -= margin

    c.drawString(x, y, c_phoneno)
    y -= margin

    c.drawString(x,y,"Special Request:")
    y -= margin

    if len(special_req) > 90:
        wrap_text = textwrap.wrap(special_req, width=90)
        for text in wrap_text:
            c.drawString(x, y, text)
            y -= margin
    elif len(special_req) <= 0:
        c.drawString(x, y, "None")
        y -= margin
    else:
        c.drawString(x, y, special_req)
        y -= margin
    y -= margin

    c.drawString(x,y,"Product")
    c.drawString(x2,y,"Quantity")
    c.drawString(x3,y,"Unite Price")
    c.drawString(x4,y,"Total")
    y -= margin

    all_total = 0
    for order in orders.values():
        product = order['name']
        price = order['price']
        quantity = order['quantity']
        total = quantity*price
        all_total += total
        quantity = str(quantity)
        price = str(price)
        total = str(total)

        c.drawString(x,y,product)
        c.drawString(x2,y,quantity)
        c.drawString(x3,y,price+" Kyat")
        c.drawString(x4,y,total+" Kyat")
        y -= margin

    c.drawString(x4,y,"Total: "+str(all_total)+" Kyat")

    #Saving the pdf file
    c.save()
    return pdf_name+".pdf"

def sent_mail(pdf_name):
    pass

@app.route('/voucher', methods=['POST'])
def voucher():
    if request.method == 'POST':
        name = request.form.get("name")
        phoneno = request.form.get("phoneno")
        address = request.form.get("address")
        special_req = request.form.get("special_req")
    order = session['order']
    pdf_name = generate_pdf(order,name,address,phoneno,special_req)
    session.modified = True
    session.clear()
    return send_file('static/orders/'+pdf_name, as_attachment=True)