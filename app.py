from flask import Flask
from routes.main import main_bp
from routes.auth import auth_bp
from routes.post import post_bp
from routes.admin import admin_bp
from routes.game import game_bp

app = Flask(__name__)
app.secret_key = 'hack_sns_secure_key'

# 블루프린트 등록
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(post_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(game_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
