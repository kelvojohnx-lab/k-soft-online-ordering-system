from flask import Blueprint, render_template, request, redirect, flash, current_app, url_for, session
import uuid

main = Blueprint('main', __name__)
def get_products():
    db = current_app.firebase_db
    prods = db.child("products").get().val()

    if not prods:
        dummy_data = {
            "1": {
                "name": "Dummy Laptop",
                "price": "40000",
                "image": url_for('static', filename='images/lp.jpg')
            },
            "2": {
                "name": "Dummy Phone",
                "price": "15000",
                "image": url_for('static', filename='images/phone.jpg')
            },
            "3": {
                "name": "Dummy Headphones",
                "price": "3500",
                "image": url_for('static', filename='images/hp.jpg')
            }
        }
        db.child("products").set(dummy_data)
        prods = dummy_data

    if isinstance(prods, list):
        prods = {str(i + 1): p for i, p in enumerate(prods)}

    valid_products = {}
    for pid, product in prods.items():
        if not product:
            continue
        if 'image' not in product or not product['image']:
            product['image'] = url_for('static', filename='images/default-product.jpg')
        valid_products[pid] = product

    return valid_products


# Home route - show login form by default
@main.route('/')
def home():
    products = get_products()  # <-- get dictionary, not function
    return render_template('home.html', products=products)


# Admin login route
@main.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        print(f"Trying admin login: {email=}, {password=}")
        print(f"Admin config: {current_app.config['ADMIN_EMAIL']=}, {current_app.config['ADMIN_PASSWORD']=}")

        if email == current_app.config['ADMIN_EMAIL'] and password == current_app.config['ADMIN_PASSWORD']:
            session['admin_user'] = email
            print(f"Admin login success. Session set: {session['admin_user']}")
            flash('Logged in as admin.', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')
            print("Admin login failed.")

    return render_template('admin_login.html')

@main.route('/admin-dashboard')
def admin_dashboard():
    # ✅ Security check: ensure only the admin can access
    admin_email = current_app.config.get('ADMIN_EMAIL')
    if session.get('admin_user') != admin_email:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.home'))

    db = current_app.firebase_db
    products_data = db.child("products").get().val() or {}

    # ✅ Normalize product data to a list with IDs attached
    products = []
    if isinstance(products_data, dict):
        for pid, pdata in products_data.items():
            pdata['id'] = pid  # 🔑 Attach Firebase key as 'id'
            products.append(pdata)

    return render_template(
        'admin_dashboard.html',
        products=products,
        admin_user=session.get('admin_user')
    )



# Add product (Admin only)
@main.route('/admin/add_product', methods=['POST'])
def add_product():
    if session.get('admin_user') != current_app.config.get('ADMIN_EMAIL'):
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.home'))

    # Remove dummy products first
    remove_dummy_products()

    data = {
        "name": request.form['name'],
        "price": request.form['price'],
        "image": request.form['image'] or url_for('static', filename='images/default-product.jpg'),
        "is_dummy": False  # mark real products explicitly
    }
    db = current_app.firebase_db
    db.child("products").push(data)

    flash('Product added.', 'success')
    return redirect(url_for('main.admin_dashboard'))


# Delete product (Admin only)
@main.route('/admin/delete_product/<pid>', methods=['POST'])
def delete_product(pid):
    if session.get('admin_user') != current_app.config.get('ADMIN_EMAIL'):
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.home'))

    db = current_app.firebase_db
    db.child("products").child(pid).remove()

    flash('Product deleted.', 'info')
    return redirect(url_for('main.admin_dashboard'))
@main.route('/admin_logout')
def admin_logout():
    session.clear()
    flash('Admin logged out.', 'info')
    return redirect(url_for('main.home'))


# User registration
@main.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    try:
        auth = current_app.firebase_auth
        user = auth.create_user_with_email_and_password(email, password)
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('main.home', form_type='login'))
    except Exception as e:
        error_json = e.args[1] if len(e.args) > 1 else str(e)
        flash(f"Registration failed: {error_json}", 'danger')
        return render_template('home.html', form_type='register')

# User login
@main.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    try:
        auth = current_app.firebase_auth
        user = auth.sign_in_with_email_and_password(email, password)
        session['user'] = user['email']
        session['user_token'] = user['idToken']
        flash('Logged in successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        error_json = e.args[1] if len(e.args) > 1 else str(e)
        flash(f"Login failed: {error_json}", 'danger')
        return render_template('home.html', form_type='login')

# User dashboard
@main.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login'))

    user_email = session['user']

    # Redirect admin user to admin dashboard
    if user_email == current_app.config['ADMIN_EMAIL']:
        return redirect(url_for('main.admin_dashboard'))

    db = current_app.firebase_db
    orders = db.child("orders").get().val() or {}

    # Filter orders belonging to current user
    user_orders = {
        oid: order for oid, order in orders.items() if order.get('user') == user_email
    }

    return render_template('dashboard.html', user=user_email, orders=user_orders)

# Products listing
@main.route('/products')
def products():
    db = current_app.firebase_db
    prods = db.child("products").get().val()

    if not prods:
        dummy_data = {
            "1": {
                "name": "Dummy Laptop",
                "price": "40000",
                "image": url_for('static', filename='images/lp.jpg')
            },
            "2": {
                "name": "Dummy Phone",
                "price": "15000",
                "image": url_for('static', filename='images/phone.jpg')
            },
            "3": {
                "name": "Dummy Headphones",
                "price": "3500",
                "image": url_for('static', filename='images/hp.jpg')
            }
        }
        db.child("products").set(dummy_data)
        prods = dummy_data

    # In case products stored as list, convert to dict with keys as string
    if isinstance(prods, list):
        prods = {str(i + 1): p for i, p in enumerate(prods)}

    valid_products = {}
    for pid, product in prods.items():
        if not product:
            continue
        if 'image' not in product or not product['image']:
            product['image'] = url_for('static', filename='images/default-product.jpg')
        valid_products[pid] = product

    return render_template('products.html', products=valid_products)

def remove_dummy_products():
    db = current_app.firebase_db
    products = db.child("products").get().val() or {}

    # Convert list to dict if necessary
    if isinstance(products, list):
        products = {str(i): prod for i, prod in enumerate(products) if prod}

    for pid, pdata in products.items():
        if pdata.get('name', '').startswith('Dummy'):
            db.child("products").child(pid).remove()



# Add product to cart
@main.route('/add_to_cart/<prod_id>')
def add_to_cart(prod_id):
    cart = session.get('cart', {})
    cart[prod_id] = cart.get(prod_id, 0) + 1
    session['cart'] = cart
    flash('Added to cart.', 'success')
    return redirect(url_for('main.products'))

# View cart
@main.route('/cart')
def cart():
    session.pop('_flashes', None)    
    if 'user' not in session:
        flash('Please login to view your cart.', 'warning')
        return redirect(url_for('main.login'))
    if session['user'] == current_app.config['ADMIN_EMAIL']:
        return redirect('Admin users cannot access the cart page.', 'danger')

    db = current_app.firebase_db
    cart = session.get('cart', {})
    items = []
    total = 0
    


    for pid, qty in cart.items():
        p = db.child("products").child(pid).get().val()
        if not p:
            continue
        price = float(p['price'])
        subtotal = price * qty
        items.append({
            'id': pid,
            'name': p['name'],
            'price': price,
            'qty': qty,
            'subtotal': subtotal
        })
        total += subtotal
    

    return render_template('cart.html', items=items, total=total)

@main.route('/update-cart/<prod_id>', methods=['POST'])
def update_cart(prod_id):
    # logic to update quantity or product info in cart
    return redirect(url_for('main.cart'))
@main.route('/remove-from-cart/<prod_id>', methods=['POST'])
def remove_from_cart(prod_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Login required', 'danger')
        return redirect(url_for('main.login'))

    cart_ref = current_app.firebase_db.child('carts').child(user_id)
    cart_ref.child(prod_id).remove()

    flash('Item removed from cart.', 'success')
    return redirect(url_for('main.cart'))


# Checkout and place order
@main.route('/checkout', methods=['POST'])
def checkout():
    if 'user_token' not in session:
        flash('Log in to place order.', 'warning')
        return redirect(url_for('main.login'))

    cart = session.get('cart', {})
    if not cart:
        flash('Cart is empty.', 'warning')
        return redirect(url_for('main.products'))

    order_id = str(uuid.uuid4())

    items_list = []
    db = current_app.firebase_db

    for pid, qty in cart.items():
        p = db.child("products").child(pid).get().val()
        if not p:
            continue
        items_list.append({
            "product_id": pid,
            "name": p['name'],
            "quantity": qty,
            "price": float(p['price'])
        })

    order = {
        'items': items_list,
        'user': session.get('user'),
        'timestamp': {'.sv': 'timestamp'}
    }

    # Save order with order_id key
    db.child("orders").child(order_id).set(order)

    session.pop('cart', None)
    flash(f'Order placed! ID: {order_id}', 'success')
    return redirect(url_for('main.dashboard'))

# Reorder previous order items into cart
@main.route('/reorder/<order_id>', methods=['POST'])
def reorder(order_id):
    if 'user' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login'))

    db = current_app.firebase_db
    order = db.child('orders').child(order_id).get().val()

    if not order or order.get('user') != session['user']:
        flash('Order not found or unauthorized.', 'danger')
        return redirect(url_for('main.dashboard'))

    cart = session.get('cart', {})

    for item in order.get('items', []):
        prod_id = item.get('product_id') or item.get('product')
        qty = item.get('quantity', 1)
        if prod_id:
            cart[prod_id] = cart.get(prod_id, 0) + qty

    session['cart'] = cart
    flash('Items from your previous order have been added to your cart.', 'success')
    return redirect(url_for('main.cart'))

# Logout user (clears session)
@main.route('/logout')
def logout():
    session.clear()  # clears all session keys, including flash messages
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

# Terminate order (user can cancel/delete order)
@main.route('/terminate_order/<order_id>', methods=['POST'])
def terminate_order(order_id):
    if 'user' not in session:
        flash('Please login to terminate an order.', 'warning')
        return redirect(url_for('main.login'))

    db = current_app.firebase_db
    order = db.child("orders").child(order_id).get().val()

    if not order or order.get('user') != session['user']:
        flash('Unauthorized or order not found.', 'danger')
        return redirect(url_for('main.dashboard'))

    db.child("orders").child(order_id).remove()
    flash('Order terminated successfully.', 'success')
    return redirect(url_for('main.dashboard'))

@main.route('/orders')
def view_orders():
    if session.get('admin_user') != current_app.config.get('ADMIN_EMAIL'):
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.home'))

    db = current_app.firebase_db
    all_orders = db.child('orders').get().val() or {}

    orders = []
    for order_id, order_data in all_orders.items():
        order_data['id'] = order_id
        orders.append(order_data)

    return render_template('orders.html', orders=orders)
