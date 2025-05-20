from flask import render_template, request, redirect, url_for, flash, jsonify, current_app as app
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Recipe
import requests
import json

def get_recipes_from_api(ingredients):
    API_KEY = 'YOUR_GEMINI_API_KEY'  # Bunu değiştir
    endpoint = 'https://api.gemini.openai.com/v1/chat/completions'

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }

    prompt = (
        f"Malzemeler: {ingredients}\n"
        "Bu malzemelerle yapılabilecek yemeklerin adını, malzemelerini ve tarifini JSON formatında listele. "
        "Her yemek için 'title', 'ingredients', 'recipe' alanları olsun."
    )

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Sen yemek tarifleri veren bir asistansın."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        res_json = response.json()
        message_content = res_json.get('choices', [{}])[0].get('message', {}).get('content', '')

        recipes = json.loads(message_content)
    except Exception as e:
        app.logger.error(f"API çağrısı hatası: {e}")
        recipes = [{'title': 'Hata', 'description': 'API çağrısında hata oluştu veya cevap işlenemedi.'}]
    return recipes


@app.route('/', methods=['GET', 'POST'])
def index():
    recipes = []
    if request.method == 'POST':
        ingredients = request.form.get('ingredients')
        if ingredients:
            recipes = get_recipes_from_api(ingredients)
        else:
            flash('Lütfen malzemeleri girin.', 'warning')
    return render_template('index.html', recipes=recipes)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Giriş başarılı.', 'success')
            return redirect(url_for('index'))
        flash('Geçersiz e-posta veya şifre.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('E-posta zaten kayıtlı.', 'warning')
        else:
            user = User(email=email, username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Kayıt başarılı, giriş yapabilirsiniz.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Çıkış yapıldı.", "info")
    return redirect(url_for('index'))


@app.route('/like/<int:recipe_id>', methods=['POST'])
@login_required
def like(recipe_id):
    # Not: API’den gelen tariflerin id yok, bu yüzden bu fonksiyon gerçek tarif veritabanı ile çalışmalı
    flash("Beğenme işlemi demo için pasif.", "info")
    return redirect(request.referrer or url_for('index'))


@app.route('/profile')
@login_required
def profile():
    # Beğeni verisi demo, gerçek projede DB’den çekilecek
    flash("Profil sayfası henüz aktif değil.", "info")
    return render_template('profile.html', recipes=[])
