from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from decimal import Decimal  # 导入 Decimal 模块
from datetime import datetime  # 新增导入 datetime 模块
import os
import json
import re
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from decimal import Decimal
from datetime import datetime
import os
import json
import re
import mimetypes  # 添加mimetypes模块用于检测文件类型

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')

# 数据库配置 - 使用Render提供的PostgreSQL数据库
database_url = "postgresql://xbjyf_user:pKaqOTvViL8ZVxFIJxcEuD2vuFE1CBvX@dpg-cv2on7lumphs739t5f6g-a.singapore-postgres.render.com/xbjyf"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# 初始化数据库
db = SQLAlchemy(app)

# 定义数据模型
class User(db.Model):
    username = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(120), nullable=False)
    register_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Product模型，包含图片数据存储
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image_data = db.Column(db.LargeBinary)  # 存储图片二进制数据
    image_name = db.Column(db.String(200))  # 存储图片名称
    stock = db.Column(db.Integer, nullable=False)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.get(username)
        if user and user.password == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return '用户名或密码错误', 403
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not re.match("^[A-Za-z0-9]+$", username):
            error = "用户名只能包含英文字母和数字"
        elif User.query.get(username):
            error = "用户名已存在"
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
            
    return render_template('register.html', error=error)

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    if search_query:
        products = Product.query.filter(Product.name.ilike(f'%{search_query}%')).all()
    else:
        products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/cart')
def cart_view():
    if 'cart' not in session:
        session['cart'] = []
    
    total_price = sum(Decimal(str(item['product']['price'])) * Decimal(str(item['quantity'])) for item in session['cart'])
    total_price = float(total_price)
    return render_template('cart.html', cart=session['cart'], total_price=total_price)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.description = request.form['description']
        product.stock = int(request.form['stock'])
        
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image_data = image.read()  # 读取图片数据
                product.image_data = image_data
                product.image_name = filename
        
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_product.html', product=product)

@app.route('/delete_user/<username>', methods=['DELETE'])
def delete_user(username):
    if 'admin' not in session:
        return jsonify({'error': '无权操作'}), 403
    
    user = User.query.get_or_404(username)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True}), 200

@app.route('/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if 'admin' not in session:
        return jsonify({'error': '无权操作'}), 403
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'success': True}), 200

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('admin', None)
    session.pop('cart', None)
    return redirect(url_for('index'))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if 'cart' not in session:
        session['cart'] = []
    
    product = Product.query.get_or_404(product_id)
    if product:
        product_dict = {
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'image_name': product.image_name,  # 修改为image_name
            'stock': product.stock
        }
        
        found = False
        for item in session['cart']:
            if item['product']['id'] == product_id:
                item['quantity'] += 1
                found = True
                break
        if not found:
            session['cart'].append({'product': product_dict, 'quantity': 1})
        session.modified = True
    return redirect(url_for('cart_view'))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' not in session:
        return redirect(url_for('cart_view'))
    
    action = request.args.get('action', 'remove')
    
    for i, item in enumerate(session['cart']):
        if item['product']['id'] == product_id:
            if action == 'reduce' and item['quantity'] > 1:
                item['quantity'] -= 1
            else:
                session['cart'].pop(i)
            break
    
    session.modified = True
    return redirect(url_for('cart_view'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if 'cart' not in session or not session['cart']:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # 处理订单逻辑
        name = request.form.get('name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        
        # 计算总价
        total_price = sum(Decimal(str(item['product']['price'])) * Decimal(str(item['quantity'])) for item in session['cart'])
        total_price = float(total_price)
        
        # 生成订单时间
        order_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 清空购物车
        session['cart'] = []
        session.modified = True
        
        return render_template('order_success.html', 
                              name=name, 
                              address=address, 
                              phone=phone, 
                              total_price=total_price,
                              order_time=order_time)
    
    total_price = sum(Decimal(str(item['product']['price'])) * Decimal(str(item['quantity'])) for item in session['cart'])
    total_price = float(total_price)
    
    return render_template('checkout.html', cart=session['cart'], total_price=total_price)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_username_input = request.form['admin_username']
        admin_password_input = request.form['admin_password']
        if admin_username_input == 'admin' and admin_password_input == '123456':
            session['admin'] = admin_username_input
            return redirect(url_for('admin_dashboard'))
        else:
            return '管理员用户名或密码错误', 403
    return render_template('admin_login.html')


# 修改Product模型
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image_data = db.Column(db.LargeBinary)  # 存储图片二进制数据
    image_name = db.Column(db.String(200))  # 存储图片名称
    stock = db.Column(db.Integer, nullable=False)

# 修改上传图片的代码
@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        
        if 'image' not in request.files:
            return '没有文件上传'
        image = request.files['image']
        
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_data = image.read()  # 读取图片数据
            
            new_product = Product(
                name=name,
                price=price,
                description=description,
                image_data=image_data,  # 存储图片数据
                image_name=filename,    # 存储图片名称
                stock=stock
            )
            db.session.add(new_product)
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        else:
            return '无效的文件格式'

# 添加一个路由来提供图片
@app.route('/product_image/<int:product_id>')
def product_image(product_id):
    product = Product.query.get_or_404(product_id)
    if not product.image_data:
        return redirect(url_for('static', filename='images/default.jpg'))
    
    # 根据文件扩展名确定MIME类型
    mime_type = mimetypes.guess_type(product.image_name)[0]
    if not mime_type:
        mime_type = 'image/jpeg'  # 默认类型
    
    response = make_response(product.image_data)
    response.headers.set('Content-Type', mime_type)
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 创建数据库表
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)