from flask import current_app as app, render_template, request, redirect, url_for, flash, jsonify
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Recipe

# Örnek Anasayfa - tarif arama ve listeleme
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        # Malzeme al, yapay zeka sorgusu yap vs.
        pass
    recipes = Recipe.query.all()
    return render_template('index.html', recipes=recipes)

# Giriş
@app.route('/login', methods=['GET', 'POST'])
def login():
    # login kodları
    pass

# Kayıt
@app.route('/register', methods=['GET', 'POST'])
def register():
    # register kodları
    pass

# Çıkış
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Çıkış yapıldı.", "info")
    return redirect(url_for('login'))

# Beğenme
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
