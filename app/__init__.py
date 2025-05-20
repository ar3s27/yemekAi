login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Giriş yapılmadıysa bu route'a gönder

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.errorhandler(401)
def unauthorized_error(error):
    flash("Bu sayfa için giriş yapmalısınız.", "warning")
    return redirect(url_for('login'))
