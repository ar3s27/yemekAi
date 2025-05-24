from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Recipe
from . import db, bcrypt
import requests
import os
from sqlalchemy.sql.expression import func
import random


bp = Blueprint('main', __name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def query_gemini(prompt_text):
    api_key = os.getenv('GEMINI_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt_text}]}]}
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    result = response.json()
    try:
        return result['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        return None

@bp.route('/', methods=['GET', 'POST'])
def index():
    ai_recipes = []
    if request.method == 'POST':
        ingredients = request.form.get('ingredients')
        if ingredients:
            # AI'dan 3 tarif iste
            ai_response = query_gemini(
                f"Malzemeler: {ingredients}. Bana birbirinden tamamen farklı 3 pratik ve lezzetli yemek tarifi öner. "
                "Her tarifi aşağıdaki formatta sırayla ve aralarına === koyarak ver:\n"
                "Başlık: ...\nHazırlanışı: ...\nİçerik: ...\n===\n"
                "Lütfen her tarifin başına 'Başlık:', hazırlanışına 'Hazırlanışı:', içeriğine 'İçerik:' yaz ve tarifleri === ile ayır. "
                "İçerik kısmı sadece malzeme listesi olsun, hazırlanışı kısmı ise adım adım yapılışı olsun."
            )
            print("AI RAW RESPONSE:\n", ai_response)  # Debug için
            recipe_blocks = [block for block in ai_response.split('===') if block.strip()][:3]
            for block in recipe_blocks:
                title, preparation, content = "", "", ""
                preparation_started = False
                content_started = False
                for line in block.strip().split('\n'):
                    if line.startswith("Başlık:"):
                        title = line.replace("Başlık:", "").strip()
                        preparation_started = False
                        content_started = False
                    elif line.startswith("Hazırlanışı:"):
                        preparation_started = True
                        content_started = False
                        preparation = line.replace("Hazırlanışı:", "").strip()
                    elif line.startswith("İçerik:"):
                        content_started = True
                        preparation_started = False
                        content = line.replace("İçerik:", "").strip()
                    elif preparation_started:
                        preparation += "\n" + line.strip()
                    elif content_started:
                        content += "\n" + line.strip()
                if not Recipe.query.filter_by(title=title).first():
                    new_recipe = Recipe(
                        title=title or "AI Tarifi",
                        description=preparation,
                        content=content
                    )
                    db.session.add(new_recipe)
                    db.session.commit()
                recipe = Recipe.query.filter_by(title=title).first()
                ai_recipes.append(recipe)
        return render_template('index.html', recipes=ai_recipes)
    # ...GET kısmı aynı kalabilir...
    else:
        show_recipes = request.args.get('show_recipes')
        if show_recipes:
            try:
                ids = [int(i) for i in show_recipes.split(',')]
                recipes = Recipe.query.filter(Recipe.id.in_(ids)).all()
                session['random_recipes'] = ids
            except:
                recipes = []
        else:
            recipe_ids = session.get('random_recipes')
            if recipe_ids:
                recipes = Recipe.query.filter(Recipe.id.in_(recipe_ids)).all()
            else:
                all_recipe_ids = [r.id for r in Recipe.query.all()]
                if all_recipe_ids:
                    random_ids = random.sample(all_recipe_ids, min(5, len(all_recipe_ids)))
                    session['random_recipes'] = random_ids
                    recipes = Recipe.query.filter(Recipe.id.in_(random_ids)).all()
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

            # Oturum açıldıktan sonra, eğer daha önce bir tarif oluşturulmuşsa, o tarife yönlendir
            last_recipe_id = session.pop('last_recipe_id', None)
            if last_recipe_id:
                return redirect(url_for('main.index', show_recipe=last_recipe_id))

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

    # Session'da kayıtlı rastgele tarif ID'leri varsa, onları show_recipe_ids olarak ekle
    random_recipes = session.get('random_recipes')
    if random_recipes:
        # URL parametresine recipe_ids dizisi ekleyelim (örn: show_recipes=1,2,3)
        ids_param = ",".join(str(rid) for rid in random_recipes)
        return redirect(url_for('main.index') + f"?show_recipes={ids_param}")
    else:
        return redirect(url_for('main.index'))


@bp.route('/unlike/<int:recipe_id>', methods=['POST'])
@login_required
def unlike(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe in current_user.liked_recipes:
        current_user.liked_recipes.remove(recipe)
        db.session.commit()
    return redirect(url_for('main.profile'))


@bp.route('/profile')
@login_required
def profile():
    liked_recipes = current_user.liked_recipes
    return render_template('profile.html', liked_recipes=liked_recipes)


@bp.route('/recipe/<int:recipe_id>')
@login_required
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('recipe_detail.html', recipe=recipe)
