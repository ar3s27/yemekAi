from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Recipe
from . import db, bcrypt
import requests
import os

bp = Blueprint('main', __name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def query_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {"parts": [{"text": f"{prompt} ile yapılabilecek bir yemek tarifi ver."}]}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    else:
        return "Yapay zeka ile tarif alınamadı."

@bp.route('/', methods=['GET', 'POST'])
def index():
    generated_recipe = None
    if request.method == 'POST':
        ingredients = request.form.get('ingredients')
        if ingredients:
            generated_recipe = query_gemini(ingredients)
            if current_user.is_authenticated and 'save' in request.form:
                new_recipe = Recipe(content=generated_recipe)
                db.session.add(new_recipe)
                current_user.liked_recipes.append(new_recipe)
                db.session.commit()
                flash("Tarif kaydedildi.", "success")
    recipes = Recipe.query.all()
    return render_template('index.html', recipes=recipes, generated_recipe=generated_recipe)

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
            flash("Giriş başarısız.", "danger")
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
            flash("Kayıt başarılı.", "success")
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
