from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Recipe
from . import db, bcrypt
import requests
import os

bp = Blueprint('main', __name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def query_gemini(prompt_text):
    api_key = os.getenv('GEMINI_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt_text}]}]
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    result = response.json()
    # Gemini API'nin dönen yapısı bazen 'candidates' altında olabilir
    try:
        return result['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        return None



@bp.route('/', methods=['GET', 'POST'])
def index():
    ai_recipe = None
    if request.method == 'POST':
        ingredients = request.form.get('ingredients')
        if ingredients:
            try:
                ai_recipe = query_gemini(f"Malzemeler: {ingredients}. Bana lezzetli ve pratik bir yemek tarifi öner.")
                flash("Tarif önerisi hazırlandı.", "success")
                if ai_recipe:
                    lines = ai_recipe.split('\n', 2)
                    ai_title = lines[0] if len(lines) > 0 else "AI Tarifi"
                    ai_description = lines[1] if len(lines) > 1 else ""
                    ai_content = ai_recipe
                    if not Recipe.query.filter_by(title=ai_title).first():
                        new_recipe = Recipe(
                            title=ai_title,
                            description=ai_description,
                            content=ai_content
                        )
                        db.session.add(new_recipe)
                        db.session.commit()
            except Exception as e:
                flash(f"Tarif alınırken hata oluştu: {str(e)}", "danger")
    recipes = Recipe.query.all()
    return render_template('index.html', recipes=recipes, ai_recipe=ai_recipe)

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
