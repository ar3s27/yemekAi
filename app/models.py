from . import db
from flask_login import UserMixin

liked_recipes = db.Table('liked_recipes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    liked_recipes = db.relationship('Recipe', secondary=liked_recipes, backref='liked_by')

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)  
    description = db.Column(db.Text, nullable=True)  
    content = db.Column(db.Text, nullable=False)


