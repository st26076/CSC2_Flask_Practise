import json
import datetime
import sqlite3
from flask import Flask, render_template, request, session, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def initialise_database():
    with sqlite3.connect('flower_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS orders (
                       order_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       invoice_number TEXT,
                       customer_name TEXT, 
                       items TEXT, 
                       addons TEXT, 
                       total REAL, 
                       date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                       ''')

@app.route('/')
def index():
    flowers, addons = load_data()
    selected_addons = session.get('selected_addons', {})
    cart = session.get('cart', {})
    total, discount_applied, flower_subtotal, addon_subtotal, original_total = calculate_total(cart, selected_addons)
    return render_template('index.html', flowers=flowers, addons=addons, cart=cart, total=total, selected_addons=selected_addons, flower_subtotal=flower_subtotal, addon_subtotal=addon_subtotal, discount_applied=discount_applied, original_total=original_total)

def load_data():
    with open('data/flowers.json') as file:
        flowers = json.load(file)
    with open('data/addons.json') as file:
        addons = json.load(file)
    return flowers, addons

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    flower = request.form['flower']
    quantity = int(request.form['quantity'])
    flowers,_ = load_data()
    cart = session.get('cart', {})

    if flower not in flowers:
        flash("Invalid flower selected.")
        return redirect(url_for('index'))
    
    if flower in cart:
        cart[flower]['quantity'] += quantity

    else:
        cart[flower] = {
            'price': flowers[flower]['price'],
            'quantity': quantity
        }

    session['cart'] = cart
    session.modified = True
    flash(f"{quantity} {flower}(s) added to cart.")
    return redirect(url_for('index'))


@app.route('/remove_from_cart/<item>')
def remove_from_cart(item):
    cart = session.get('cart', {})

    if item in cart:
        del cart[item]
        session['cart'] = cart
        session.modified = True
        flash(f"Removed all {item.capitalize()} from cart.")
    else:
        flash("Item not found in cart")

    return redirect(url_for('index'))

@app.route('/select_addon', methods=['POST'])
def select_addon():
    selected_addons = {}
    _, addons = load_data()

    selected_keys = request.form.getlist('addons')

    for addon in selected_keys:
        if addon in addons:
            selected_addons[addon] = {
                'price': addons[addon]['price']
            }
    if not selected_keys:
        flash("Invalid addon selected.")
        return redirect(url_for('index'))
    
    if addon in selected_addons:
        selected_addons[addon]
    
    else: selected_addons[addon] = {
        'price': addons[addon]['price']
    }
        
    session['selected_addons'] = selected_addons
    session.modified = True
    flash(f"{addon}(s) added to cart.")
    return redirect(url_for('index'))

def flower_subtotal(cart):
    total = sum (item['price'] * item['quantity'] for item in cart.values())
    return total

def addon_subtotal(selected_addons):
    total = sum (item['price'] for item in selected_addons.values())
    return total

def calculate_total(cart, selected_addons):
    flower_subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    addon_subtotal = sum(item['price'] for item in selected_addons.values())
    original_total = flower_subtotal + addon_subtotal
    total = original_total
    discount_applied = False
    if total > 180:
        total = total * 0.9
        discount_applied = True
    return total, discount_applied, flower_subtotal, addon_subtotal, original_total

@app.route('/checkout', methods=['POST'])
def checkout():
    customer_name = request.form['customer_name'].strip().title()
    if not customer_name:
        flash("Customer name is required.")
        return redirect(url_for('index'))

    cart = session.get('cart', {})
    selected_addons = session.get('selected_addons', {})    
    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for('index'))
    
    total, discount_applied, flower_subtotal, addon_subtotal, original_total = calculate_total(cart, selected_addons)    
    invoice_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    invoice_number = f"INV_{customer_name.replace(' ', '_')}_{invoice_date}"

    with sqlite3.connect('flower_shop.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           INSERT INTO orders (invoice_number, customer_name, items, addons, total)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (invoice_number, customer_name, json.dumps(cart), json.dumps(selected_addons), total))
            conn.commit()


    invoice_filename = f"{invoice_number.replace(':', '-')}.txt"    
    with open(invoice_filename, 'w') as f:
        f.write("----- Flower Shop Invoice -----\n\n")
        f.write(f"Invoice Number: {invoice_number}\n")
        f.write(f"Customer Name: {customer_name}\n")
        f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("Items:\n")
        for item, details in cart.items():
            f.write(f"-{item}: {details['quantity']} x ${details['quantity'] * details['price']:.2f}\n")
        if selected_addons:
            f.write("\nAdd-Ons:\n")
            for addon, price in selected_addons.items():
                f.write(f"-{addon}: ${details['price']:.2f}\n")
        f.write(f"\nTotal: ${total:.2f}\n")

    with open('data/flowers.json', 'r') as file:
        flower_data = json.load(file)

    for flower_name, details in cart.items():
        if flower_name in flower_data:
            flower_data[flower_name]['stock'] -= details['quantity']
            if flower_data[flower_name]['stock'] < 0:
                flower_data[flower_name]['stock'] = 0 

    with open('data/flowers.json', 'w') as file:
        json.dump(flower_data, file, indent=4)
    session.pop('cart', None)
    session.pop('selected_addons', None)
    session.modified = True
    return render_template('invoices.html', customer_name=customer_name, total=total, invoice_date=invoice_date, invoice_number=invoice_number, cart=cart, selected_addons=selected_addons, flower_subtotal=flower_subtotal, addon_subtotal=addon_subtotal, invoice_filename=invoice_filename, discount_applied=discount_applied, original_total=original_total)


@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    session.pop('cart', None)
    session.pop('selected_addons', None)
    session.modified = True
    flash("Order cancelled. Your cart has been emptied")
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/order_history')
def order_history():
    with sqlite3.connect('flower_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders ORDER BY date DESC")
        rows = cursor.fetchall()
        orders = []
        for row in rows:
            orders.append ({'order_id': row[0],'invoice_number': row[1], 'customer_name': row [2],'items': json.loads(row[3]),'addons': json.loads(row[4]),'total': row[5], 'date': row[6] })
    return render_template('order_history.html', orders=orders)

@app.route('/cancel_saved_order/<int:order_id>', methods=['POST'])
def cancel_saved_order(order_id):
    with sqlite3.connect('flower_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        conn.commit()
    flash("Order Cancelled.")
    return redirect(url_for('order_history'))

@app.route('/invoices')
def invoices():
    return render_template('invoices.html')

if __name__ == '__main__':
    initialise_database()
    app.run(debug=True)