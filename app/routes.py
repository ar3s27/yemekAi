from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Recipe
from . import db, bcrypt
import requests
import os
from .gemini_api import query_gemini


bp = Blueprint('main', __name__)

def get_recipes_from_gemini(ingredients):
    api_key = os.getenv("GEMINI_API_KEY")
    url = "https://api.gemini.ai/v1/text/completions"  # Gemini 2.0 Flash endpoint'i
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gemini-2.0-flash",
        "prompt": f"{ingredients} ile yapılabilecek yemek tariflerini listele.",
        "max_tokens": 500,
        "temperature": 0.7,
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        # API yanıt yapısına göre uyarlayabilirsin
        text = data['completions'][0]['data']['text']
        # Satır satır tarifleri ayır
        recipes = [line.strip() for line in text.split('\n') if line.strip()]
        return recipes
    else:
        print(f"Gemini API error: {response.status_code} {response.text}")
        return []

@bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ingredients = request.form.get('ingredients')
        recipe_text = None
        if ingredients:
            recipe_text = query_gemini(f"Malzemeler: {ingredients}. Bana lezzetli bir yemek tarifi öner.")
            flash("Tarif önerisi hazırlandı.", "success")
        recipes = Recipe.query.all()
        return render_template('index.html', recipes=recipes, ai_recipe=recipe_text)
    else:
        recipes = Recipe.query.all()
        return render_template('index.html', recipes=recipes)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Başarıyla giriş yapıldı.", "success")
            return redirect(url_for('main.index'))
        else:
            flash("Giriş başarısız, bilgilerinizi kontrol edin.", "danger")
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash("Bu e-posta zaten kayıtlı.", "warning")
        else:
            hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, email=email, password_hash=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            flash("Kayıt başarılı, giriş yapabilirsiniz.", "success")
            return redirect(url_for('main.login'))
    return render_template('register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Çıkış yapıldı.", "info")
    return redirect(url_for('main.login'))

@bp.route('/like/<int:recipe_id>', methods=['POST'])
@login_required
def like(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe in current_user.liked_recipes:
        current_user.liked_recipes.remove(recipe)
        flash("Beğeni kaldırıldı.", "info")
    else:
        current_user.liked_recipes.append(recipe)
        flash("Tarif beğenildi.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    recipes = current_user.liked_recipes
    return render_template('profile.html', recipes=recipes)
