import requests
from flask import Blueprint, request, jsonify
from app import db
from app.models import User

google_auth_bp = Blueprint("google_auth", __name__)

@google_auth_bp.route("/callback", methods=["POST"])
def google_callback():
    data = request.get_json()
    token = data.get("token")

    google_url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token}"
    response = requests.get(google_url).json()

    email = response.get("email")
    firstname = response.get("given_name")
    lastname = response.get("family_name")

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(firstname=firstname, lastname=lastname, email=email, provider="google")
        db.session.add(user)
        db.session.commit()

    return jsonify({"message": "Login successful", "user": {"email": email}})
