from flask import Flask, request, redirect, render_template
import sqlite3
import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "db.sqlite")
context = {}
personal_info = {}

app = Flask(__name__)


@app.route('/')
def main():
    return render_template("index.html", **context)


@app.route('/shop/')
def shop():
    return render_template("shop.html", **context)


@app.route('/personal/')
def personal():
    if not context.get('Name'):
        return redirect("http://localhost:5000/login/", code=302)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''select first_name, second_name, email, phone from users where email = ?;''',
                (context.get('login'),))
    pers_tuple = cur.fetchall()[0]
    print(pers_tuple)
    first_name, second_name, email, phone = pers_tuple[0], pers_tuple[1], pers_tuple[2], pers_tuple[3]
    print(second_name)
    personal_info.update({
        'first_name': first_name,
        'second_name': second_name,
        'email': email,
        'phone': phone
    })
    conn.close()

    return render_template("personal.html", **context, **personal_info)


@app.route('/details/')
def details():
    return render_template("details.html", **context)


@app.route('/logout/')
def logout():
    context.update({'login': '', 'Name': ''})
    return redirect("http://localhost:5000/login/", code=302)


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


if __name__ == '__main__':
    app.run()
