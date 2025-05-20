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
            db.session
