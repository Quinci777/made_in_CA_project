from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

# app initialization with custom template folder
template_dir = os.path.abspath('../Frontend')
app = Flask(__name__, template_folder=template_dir)

# app configuration
# check if secret key is set
load_dotenv()
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise ValueError("SECRET_KEY не установлен! Пожалуйста, добавьте его в .env файл.")
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Path to SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable SQLAlchemy modification tracking

# Database initialization
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.login}>'

# Create the database tables if they don't exist
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registration', methods=['POST'])
def registration():
    # receive user input
    login = request.form.get('login')
    password = request.form.get('password')

    if not login or not password:
        flash("Пожалуйста, заполните все поля для регистрации.")
        return redirect(url_for('index'))

    # check if user already exists
    existing_user = User.query.filter_by(login=login).first()
    if existing_user:
        flash("Пользователь с таким логином уже существует.")
        return redirect(url_for('index'))

    # hash the password
    hashed_password = generate_password_hash(password)

    # create a new user
    new_user = User(login=login, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    flash("Регистрация прошла успешно! Теперь вы можете войти.")
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    login_value = request.form.get('login')
    password = request.form.get('password')

    # find user by login
    user = User.query.filter_by(login=login_value).first()

    # check if user exists and password is correct
    if user and check_password_hash(user.password_hash, password):
        flash("Вход выполнен успешно!")
        # store user id in session:
        # session['user_id'] = user.id
    else:
        flash("Неверный логин или пароль.")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
