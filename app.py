import json
from flask import Flask, render_template, request, session, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    flowers, addons = load_data()
    selected_addons = session.get('selected_addons', {})
    cart = session.get('cart', {})
    total, flower_subtotal, addon_subtotal = calculate_total(cart, selected_addons)
    return render_template('index.html', flowers=flowers, addons=addons, cart=cart, total=total, selected_addons=selected_addons, flower_subtotal=flower_subtotal, addon_subtotal=addon_subtotal)

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
    flower_subtotal = sum (item['price'] * item['quantity'] for item in cart.values())
    addon_subtotal = sum (item['price'] for item in selected_addons.values())
    total = flower_subtotal + addon_subtotal
    return total, flower_subtotal, addon_subtotal

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
    return render_template('order_history.html')

@app.route('/invoices')
def invoices():
    return render_template('invoices.html')

if __name__ == '__main__':
    app.run(debug=True)