from flask import Blueprint, request, jsonify
from models.sql_models import User, Client  # Import both User and Client
from config import Config
from database import db
import jwt
import uuid
import logging
from helpers.cors_helpers import pre_authorized_cors_preflight
from datetime import datetime, timezone, timedelta

current_time = datetime.now(timezone.utc)

auth_bp = Blueprint('auth_bp', __name__)

# Utility function to create JWT payload
def create_jwt_token(identifier, email_or_access_key, expires_in_hours=1):
    """
    For users, identifier might be user_uuid and email_or_access_key is email.
    For clients, identifier might be client code and email_or_access_key is access_key.
    """
    payload = {
        "id": identifier,
        "value": email_or_access_key,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

# ----- Sign-up Endpoint -----
@auth_bp.route('/signup', methods=['POST', 'OPTIONS'])
@pre_authorized_cors_preflight
def signup():
    data = request.get_json()
    logging.debug('Received signup request with data: %s', data)

    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')

    if not first_name or not last_name or not email or not password:
        logging.warning('Missing required fields in signup request')
        return jsonify({"error": "First name, last name, email, and password are required"}), 400

    # Check if user already exists
    existing_user = db.session.query(User).filter(User.email == email).first()
    if existing_user:
        logging.warning('User with email %s already exists', email)
        return jsonify({"error": "User with that email already exists"}), 409

    # Create a new user
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        user_uuid=str(uuid.uuid4())
    )
    new_user.set_password(password)  # Hash password
    logging.debug('Created new user object for email: %s', email)

    try:
        db.session.add(new_user)
        db.session.commit()
        logging.info('User with email %s created successfully', email)

        # Generate a short-lived access token (no refresh token)
        access_token_str = create_jwt_token(new_user.user_uuid, new_user.email, expires_in_hours=1)

        return jsonify({
            "message": "User created successfully",
            "user_uuid": new_user.user_uuid,
            "user_id": new_user.id,
            "email": new_user.email,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "access_token": access_token_str,
        }), 201
    except Exception as e:
        db.session.rollback()
        logging.error('Failed to create user with email %s: %s', email, str(e))
        return jsonify({"error": f"Failed to create user: {str(e)}"}), 500

# ----- User Sign-in Endpoint -----
@auth_bp.route('/signin', methods=['POST', 'OPTIONS'])
@pre_authorized_cors_preflight
def signin():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Query the database for the user
    user = db.session.query(User).filter(User.email == email).first()
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token_str = create_jwt_token(user.user_uuid, user.email, expires_in_hours=1)

    return jsonify({
        "message": "Sign-in successful",
        "user_uuid": user.user_uuid,
        "user_id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "access_token": access_token_str
    }), 200

# ----- Client Sign-in Endpoint -----
@auth_bp.route('/client-signin', methods=['POST', 'OPTIONS'])
@pre_authorized_cors_preflight
def client_signin():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    client_code = data.get('client_code')
    access_key = data.get('access_key')

    if not client_code or not access_key:
        return jsonify({"error": "Client code and access key are required"}), 400

    # Normalize the values to uppercase to match stored values
    normalized_code = client_code.strip().upper()
    normalized_access_key = access_key.strip().upper()

    client = db.session.query(Client).filter(Client.code == normalized_code).first()
    if not client:
        return jsonify({"error": "Invalid credentials"}), 401

    # Compare stored access key (also uppercased) with provided value
    if client.access_key.upper() != normalized_access_key:
        return jsonify({"error": "Invalid credentials"}), 401

    # Generate a short-lived access token for client sign-in
    access_token_str = create_jwt_token(client.code, client.access_key, expires_in_hours=1)

    return jsonify({
        "message": "Client sign-in successful",
        "client_id": client.id,
        "code": client.code,
        "login_link": client.login_link,
        "access_key": client.access_key,
        "access_token": access_token_str
    }), 200
