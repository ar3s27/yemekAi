from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, logout_user, current_user, login_required
from . import app, db
from .models import User, Recipe
from .gemini_utils import get_recipe_from_gemini

@app.route('/', methods=['GET', 'POST'])
def index():
    recipe = None
    if request.method == 'POST':
        ingredients = request.form.get('ingredients')
        if ingredients:
            # Yapay zeka ile tarif al
            response = get_recipe_from_gemini(ingredients)
            if response:
                # Veritabanına kaydet
                new_recipe = Recipe(title=f"Tarif: {ingredients}", content=response)
                db.session.add(new_recipe)
                db.session.commit()
                recipe = new_recipe
            else:
                flash("Tarif alınamadı, tekrar deneyin.", "danger")
    return render_template('index.html', recipe=recipe)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash("Kullanıcı adı zaten var.", "danger")
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Kayıt başarılı, giriş yapabilirsiniz.", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Giriş başarılı.", "success")
            return redirect(url_for('index'))
        else:
            flash("Giriş başarısız. Kullanıcı adı veya şifre yanlış.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    flash("Çıkış yapıldı.", "info")
    return redirect(url_for('index'))

@app.route('/like/<int:recipe_id>', methods=['POST'])
@login_required
def like(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe in current_user.liked_recipes:
        current_user.liked_recipes.remove(recipe)
        flash("Tarif beğenme kaldırıldı.", "info")
    else:
        current_user.liked_recipes.append(recipe)
        flash("Tarif beğenildi.", "success")
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    liked = current_user.liked_recipes
    return render_template('profile.html', recipes=liked)
