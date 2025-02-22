import smtplib
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
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
    print("WARNING: SECRET_KEY не установлен! Пожалуйста, добавьте его в .env файл.")
app.config['SECRET_KEY'] = secret_key
app.config['BASE_URL'] = os.getenv('BASE_URL')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Path to SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable SQLAlchemy modification tracking
# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
# Initialize Flask-Mail
mail = Mail(app)

# Database initialization
db = SQLAlchemy(app)
# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email_confirmed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User {self.email}>'

# Create the database tables if they don't exist
with app.app_context():
    db.create_all()

# Default route and form handling
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registration', methods=['POST'])
def registration():
    # receive user input
    user_password = request.form.get('password')
    user_email = request.form.get('email')

    if not user_password or not user_email:
        flash("Пожалуйста, заполните все поля для регистрации.")
        return redirect(url_for('index'))

    # check if password is strong enough
    if len(user_password) < 8:
        flash("Пароль должен содержать не менее 8 символов.")
        return redirect(url_for('index'))

    # check if user already exists
    existing_email = User.query.filter_by(email=user_email).first()
    if existing_email:
        flash("Пользователь с такой электронной почтой уже существует.")
        return redirect(url_for('index'))
    
    # check if email is not valid
    if '@' not in user_email or '.' not in user_email:
        flash("Неверный формат электронной почты.")
        return redirect(url_for('index'))

    # hash the password
    hashed_password = generate_password_hash(user_password)

    # create a new user
    new_user = User(password_hash=hashed_password, email=user_email, email_confirmed=False)
    db.session.add(new_user)
    db.session.commit()

    # send confirmation email
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = serializer.dumps(new_user.email, salt='email-confirm')
    confirm_url = f"{app.config['BASE_URL']}/confirm_email/{token}"
    subject = "Подтверждение регистрации"
    body = f"Пожалуйста, перейдите по ссылке для подтверждения регистрации: {confirm_url}"
    send_email(new_user.email, subject, body)
    flash("На вашу почту отправлена ссылка для подтверждения регистрации!")
    return redirect(url_for('index'))

# Email confirmation route
@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = URLSafeTimedSerializer(app.config['SECRET_KEY']).loads(token, salt='email-confirm', max_age=3600)
    except:
        flash("Ссылка для подтверждения регистрации недействна или истекла.")
        return redirect(url_for('index'))

    user = User.query.filter_by(email=email).first()
    if user:
        user.email_confirmed = True
        db.session.commit()
        flash("Регистрация подтверждена успешно! Теперь вы можете входить в систему.")
    else:
        flash("Пользователь не найден.")
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    email_value = request.form.get('email')
    password_value = request.form.get('password')

    # find user by login
    user = User.query.filter_by(email=email_value).first()

    # check if user exists and password is correct
    if user and check_password_hash(user.password_hash, password_value):
        flash("Вход выполнен успешно!")
        # store user id in session:
        # session['user_id'] = user.id
    else:
        flash("Неверная почта или пароль.")

    return redirect(url_for('index'))

# Email sending function
def send_email(to, subject, body):
    msg = Message(subject, recipients=[to], body=body)
    mail.send(msg)

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=8080)