from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Allow all origins (Remove restrictions)
    CORS(app, supports_credentials=True, origins="*")

    # Handle preflight requests for signin
    @app.route("/signin", methods=["OPTIONS"])
    def signin_preflight():
        return jsonify({"message": "Preflight OK"}), 200

    from app.routes import auth_bp, playlist_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(playlist_bp, url_prefix="/playlists")  # ✅ Register Playlist routes

    return app
