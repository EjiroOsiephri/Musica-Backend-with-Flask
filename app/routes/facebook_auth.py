import requests
from flask import Blueprint, request, jsonify
from app import db
from app.models import User
import os

facebook_auth_bp = Blueprint("facebook_auth", __name__)

@facebook_auth_bp.route("/callback", methods=["POST"])
def facebook_callback():
    data = request.get_json()
    access_token = data.get("access_token")

    facebook_url = f"https://graph.facebook.com/me?fields=id,first_name,last_name,email&access_token={access_token}"
    response = requests.get(facebook_url).json()

    email = response.get("email")
    firstname = response.get("first_name")
    lastname = response.get("last_name")

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(firstname=firstname, lastname=lastname, email=email, provider="facebook")
        db.session.add(user)
        db.session.commit()

    return jsonify({"message": "Login successful", "user": {"email": email}})
