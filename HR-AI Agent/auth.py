import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, User, mail

auth_bp = Blueprint('auth', __name__, template_folder='templates')

# Страница входа
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if not current_user.email_confirmed:
            logout_user()
            flash("Подтвердите email перед входом", 'warning')
            return redirect(url_for('auth.login'))
        return redirect(url_for('main.form'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Неверный email или пароль', 'error')
            return redirect(url_for('auth.login'))

        if not user.email_confirmed:
            flash('Подтвердите email перед входом', 'warning')
            return redirect(url_for('auth.login'))

        login_user(user)
        flash('Вы успешно вошли!', 'success')
        return redirect(url_for('main.form'))

    return render_template('login.html')

# Страница регистрации
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.form'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Заполните все поля", 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash("Данный email уже зарегистрирован", 'error')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password_hash=hashed_password)
        db.session.add(new_user)
        logout_user()
        db.session.commit()

        # Отправка письма с подтверждением
        serializer = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))
        token = serializer.dumps(email, salt='email-confirm')
        link = f"{os.getenv('BASE_URL')}/confirm_email/{token}"
        send_email(email, "Подтверждение регистрации", f"Перейдите по ссылке: {link}")

        flash("Ссылка для подтверждения отправлена на вашу почту", 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# Подтверждение email
@auth_bp.route('/confirm_email/<token>')
def confirm_email(token):
    serializer = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except:
        flash("Ссылка недействительна или истекла", 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()
    if user:
        user.email_confirmed = True
        db.session.commit()
        flash("Email подтверждён. Теперь вы можете войти", 'success')

    return redirect(url_for('auth.login'))

# Выход из системы
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('auth.login'))

# Страница профиля
@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


# Утилита отправки писем
def send_email(to, subject, body):
    msg = Message(subject, recipients=[to], body=body)
    mail.send(msg)