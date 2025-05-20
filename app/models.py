from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

liked_recipes = db.Table('liked_recipes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password_hash = db.Column(db.String(256))
    liked_recipes = db.relationship('Recipe', secondary=liked_recipes, backref='liked_by')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    ingredients = db.Column(db.Text)
    instructions = db.Column(db.Text)
