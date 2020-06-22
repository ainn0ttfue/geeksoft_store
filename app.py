from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route('/')
def main():
    return render_template("index.html")


@app.route('/shop/')
def shop():
    return render_template("shop.html")


@app.route('/personal/')
def personal():
    return render_template("personal.html")


@app.route('/details/')
def details():
    return render_template("details.html")


if __name__ == '__main__':
    app.run()
