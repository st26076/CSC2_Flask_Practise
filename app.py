import json
from flask import Flask, render_template, request, session, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    flowers, addons = load_data()
    selected_addons = session.get('selected_addons', {})
    cart = session.get('cart', {})
    total = calculate_total(cart)
    return render_template('index.html', flowers=flowers, addons=addons, cart=cart, total=total, selected_addons=selected_addons)

def load_data():
    with open('data/flowers.json') as file:
        flowers = json.load(file)
    with open('data/addons.json') as file:
        addons = json.load(file)
    return flowers, addons

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    flower = request.form['flower']
    addon = request.form['addon']
    quantity = int(request.form['quantity'])
    flowers, addons = load_data()
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

def calculate_total(cart):
    total = sum (item['price'] * item['quantity'] for item in cart.values())
    return total

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/order_history')
def order_history():
    return render_template('order_history.html')

@app.route('/invoices')
def invoices():
    return render_template('invoices.html')

@app.route('/select_addon', methods=['POST'])
def select_addon():
    selected_addons = {}
    _, addons = load_data()

    selected_keys = request.form.getlist('addons')

    for addon in selected_keys:
        if addon in addons:
            selected_addons[addon] = float(addons[addon]['price'])

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

if __name__ == '__main__':
    app.run(debug=True)