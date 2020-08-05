from flask import Flask, request, redirect, render_template
import sqlite3
import os.path
from random import shuffle

# Путь для подключения базы данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "db.sqlite")

context = {}
personal_info = {}

app = Flask(__name__)


@app.route('/')
def main():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Вывод товаров
    cur.execute('''select title, image_url, price from products;''')
    products = []
    for item in cur.fetchall():
        products.append(list(item))
    shuffle(products)
    context.update({'products': products})

    # Вывод категорий товаров
    cur.execute("select title from categories;")
    categories_list = []
    for item in cur.fetchall():
        categories_list.append(item[0])
    context.update({'categories': categories_list})

    conn.close()
    return render_template("index.html", **context)


@app.route('/shop/', methods=['POST', 'GET'])
def shop():
    if request.method == 'POST':
        # Фильтр - крайний порог цены
        context.update({'max_value': request.form.get('max_value_count')})
        # Фильтр - цена по возрастанию или убыванию
        sort_price = request.form.get('sort_price')
    else:
        context.update({'max_value': 960})
        sort_price = ''

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Если пользоавтель ввел запрос в строку поиска
    if request.args.get('text'):
        context.update({'search_text': request.args.get('text')})
    else:
        context.update({'search_text': ' '})

    execute = "select title, image_url, price, id from products WHERE price <= " + str(context.get('max_value')) + " union select title, image_url, price, id from products WHERE price <= " + str(context.get('max_value')) + " order by price " + sort_price + " ;"
    cur.execute(execute)

    products = []
    for item in cur.fetchall():
        products.append(list(item))

    # Исключение товаров, в которых нет ключевых слов из поискового запроса
    products = [item for item in products if context.get('search_text').lower() in item[0] or context.get('search_text').title() in item[0]]

    # Вывод категорий товаров
    cur.execute("select title from categories;")
    categories_list = []
    for item in cur.fetchall():
        categories_list.append(item[0])
    context.update({'categories': categories_list})

    # Если пользователь открыл товары из категории
    if request.args.get('category'):
        cur.execute("""select product_id from categories_products where cat_id = (select id from categories where title = ?);""", (request.args.get('category'),))
        sort_categories = []
        for item in cur.fetchall():
            sort_categories.append(item[0])

        # Исключение товаров, которые не соответствуют выбранной категории
        products = [item for item in products if item[3] in sort_categories]
    context.update({'products': products})
    conn.close()

    return render_template("shop.html", **context)


@app.route('/personal/')
def personal():
    if not context.get('Name'):
        return redirect("/login/", code=302)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''select first_name, second_name, email, phone from users where email = ?;''',
                (context.get('login'),))
    pers_tuple = cur.fetchall()[0]
    first_name, second_name, email, phone = pers_tuple[0], pers_tuple[1], pers_tuple[2], pers_tuple[3]
    personal_info.update({
        'first_name': first_name,
        'second_name': second_name,
        'email': email,
        'phone': phone
    })

    cur.execute('''select title, image_url, price from products;''')
    products = []
    for item in cur.fetchall():
        products.append(list(item))
    shuffle(products)
    context.update({'products': products})
    conn.close()

    return render_template("personal.html", **context, **personal_info)


@app.route('/details/')
def details():
    if not request.args.get('title'):
        return redirect("/shop/", code=302)
    product_title = request.args.get('title')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        '''select image_url, price, count, mini_description, specifications, description from products where title = ?;''',
        (product_title,))
    product_info = list(cur.fetchall()[0])
    product_info.insert(0, product_title)
    context.update({'current_product': product_info})

    cur.execute('''select title, image_url, price from products;''')
    products = []
    for item in cur.fetchall():
        products.append(list(item))
    shuffle(products)
    context.update({'products': products})

    conn.close()
    return render_template("details.html", **context)


@app.route('/logout/')
def logout():
    context.update({'login': '', 'Name': ''})
    return redirect("/login/", code=302)


@app.route('/signup/', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        second_name = request.form.get('second_name')
        email = request.form.get('email')
        tel = request.form.get('tel')
        password = request.form.get('password')

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute('''select * from users where email = ? or phone = ?;''', (email, tel))
        if cur.fetchall():
            context.update({'signup_alert': '<span class="text-danger">Такой пользователь уже существует</span>'})
        else:
            cur.execute(
                '''insert into users (first_name, second_name, email, phone, password) values (?, ?, ?, ?, ?);''',
                (first_name, second_name, email, tel, password))
            conn.commit()
            context.update({'signup_alert': '<span class="text-success">Регистрация прошла успешно</span>'})
            context.update({'login': email, 'Name': first_name})
            return redirect("http://localhost:5000/personal/", code=302)
        conn.close()
    else:
        context.update({'signup_alert': ''})
    return render_template("registr.html", **context)


@app.route('/login/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute('''select * from users where email = ? and password = ?;''', (email, password))
        if cur.fetchall():
            context.update({'login_alert': '<span class="text-success">Вход совершен</span>'})
            cur.execute('''select first_name from users where email = ?;''', (email,))
            # first_name =  ['Name']. => Name
            first_name = str(cur.fetchall())[3:-4]
            context.update({'login': email, 'Name': first_name})
            return redirect("http://localhost:5000/personal/", code=302)
        else:
            context.update({'login_alert': '<span class="text-danger">Неправильный Логин и/или Пароль</span>'})
        conn.close()
    else:
        context.update({'login_alert': ''})

    return render_template("login.html", **context)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run()
