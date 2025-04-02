import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from models.sql_models import Building
from database import db
from helpers.cors_helpers import pre_authorized_cors_preflight

building_bp = Blueprint('building_bp', __name__)

# ----------------------------------------
# 1. GET All Buildings (with optional search)
# ----------------------------------------
@building_bp.route("/buildings", methods=["GET"])
@pre_authorized_cors_preflight
def get_all_buildings():
    search = request.args.get('search', '')
    try:
        query = db.session.query(Building)
        if search:
            query = query.filter(Building.name.ilike(f"%{search}%"))
        buildings = query.all()
        if not buildings:
            return jsonify({"message": "No buildings found"}), 404

        building_list = []
        for b in buildings:
            building_data = {
                "id": b.id,
                "name": b.name,
                "year_built": b.year_built,
                "nearest_bts": b.nearest_bts,
                "nearest_mrt": b.nearest_mrt,
                "distance_to_bts": float(b.distance_to_bts) if b.distance_to_bts is not None else None,
                "distance_to_mrt": float(b.distance_to_mrt) if b.distance_to_mrt is not None else None,
                "facilities": b.facilities,
                "photo_urls": b.photo_urls,
                "created_at": b.created_at.strftime('%Y-%m-%d %H:%M:%S') if b.created_at else None,
            }
            building_list.append(building_data)
        return jsonify(building_list), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch buildings: {str(e)}"}), 500

# ----------------------------------------
# 2. GET Building by ID
# ----------------------------------------
@building_bp.route("/buildings/<int:building_id>", methods=["GET"])
@pre_authorized_cors_preflight
def get_building(building_id):
    try:
        b = db.session.query(Building).filter(Building.id == building_id).first()
        if not b:
            return jsonify({"error": "Building not found"}), 404

        building_data = {
            "id": b.id,
            "name": b.name,
            "year_built": b.year_built,
            "nearest_bts": b.nearest_bts,
            "nearest_mrt": b.nearest_mrt,
            "distance_to_bts": float(b.distance_to_bts) if b.distance_to_bts is not None else None,
            "distance_to_mrt": float(b.distance_to_mrt) if b.distance_to_mrt is not None else None,
            "facilities": b.facilities,
            "photo_urls": b.photo_urls,
            "created_at": b.created_at.strftime('%Y-%m-%d %H:%M:%S') if b.created_at else None,
        }
        return jsonify(building_data), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch building: {str(e)}"}), 500

# ----------------------------------------
# 3. CREATE a New Building
# ----------------------------------------
@building_bp.route("/buildings", methods=["POST"])
@pre_authorized_cors_preflight
def create_building():
    data = request.get_json()
    try:
        new_building = Building(
            name=data.get("name"),
            year_built=int(data["year_built"]) if data.get("year_built") else None,
            nearest_bts=data.get("nearest_bts"),
            nearest_mrt=data.get("nearest_mrt"),
            distance_to_bts=float(data["distance_to_bts"]) if data.get("distance_to_bts") else None,
            distance_to_mrt=float(data["distance_to_mrt"]) if data.get("distance_to_mrt") else None,
            facilities=data.get("facilities"),  # Expecting JSON or a stringified JSON
            photo_urls=data.get("photo_urls")     # Expecting JSON or a stringified JSON
        )
        db.session.add(new_building)
        db.session.commit()
        return jsonify({
            "message": "Building created successfully",
            "building_id": new_building.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create building: {str(e)}"}), 500

# ----------------------------------------
# 4. UPDATE a Building
# ----------------------------------------
@building_bp.route("/buildings/<int:building_id>", methods=["PUT"])
@pre_authorized_cors_preflight
def update_building(building_id):
    data = request.get_json()
    try:
        b = db.session.query(Building).filter(Building.id == building_id).first()
        if not b:
            return jsonify({"error": "Building not found"}), 404

        b.name = data.get("name", b.name)
        b.year_built = int(data["year_built"]) if data.get("year_built") else b.year_built
        b.nearest_bts = data.get("nearest_bts", b.nearest_bts)
        b.nearest_mrt = data.get("nearest_mrt", b.nearest_mrt)
        b.distance_to_bts = float(data["distance_to_bts"]) if data.get("distance_to_bts") else b.distance_to_bts
        b.distance_to_mrt = float(data["distance_to_mrt"]) if data.get("distance_to_mrt") else b.distance_to_mrt
        b.facilities = data.get("facilities", b.facilities)
        b.photo_urls = data.get("photo_urls", b.photo_urls)

        db.session.commit()
        return jsonify({"message": "Building updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update building: {str(e)}"}), 500

# ----------------------------------------
# 5. DELETE a Building
# ----------------------------------------
@building_bp.route("/buildings/<int:building_id>", methods=["DELETE"])
@pre_authorized_cors_preflight
def delete_building(building_id):
    try:
        b = db.session.query(Building).filter(Building.id == building_id).first()
        if not b:
            return jsonify({"error": "Building not found"}), 404

        db.session.delete(b)
        db.session.commit()
        return jsonify({"message": "Building deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete building: {str(e)}"}), 500
