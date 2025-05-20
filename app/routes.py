from flask import current_app as app, render_template, request, redirect, url_for, flash, jsonify
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Recipe
from werkzeug.security import check_password_hash, generate_password_hash

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        # Malzeme al, yapay zeka sorgusu yap vs.
        pass
    recipes = Recipe.query.all()
    return render_template('index.html', recipes=recipes)

# ✅ Giriş yapma
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Giriş başarılı!", "success")
            return redirect(url_for('index'))
        else:
            flash("Kullanıcı adı veya şifre hatalı.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# ✅ Kayıt olma
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Bu kullanıcı adı zaten alınmış.", "warning")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Kayıt başarılı! Giriş yapabilirsiniz.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# Çıkış
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Çıkış yapıldı.", "info")
    return redirect(url_for('login'))

# Tarif beğenme
@app.route('/like/<int:recipe_id>', methods=['POST'])
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
    return redirect(request.referrer or url_for('index'))

# Profil sayfası
@app.route('/profile')
@login_required
def profile():
    recipes = current_user.liked_recipes
    return render_template('profile.html', recipes=recipes)
