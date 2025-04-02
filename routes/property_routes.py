import os
import uuid
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from models.sql_models import Property, Building
from database import db
from helpers.cors_helpers import pre_authorized_cors_preflight
import boto3
from dotenv import load_dotenv
from sqlalchemy.orm import joinedload

# Load .env file
load_dotenv()

# Read Cloudflare R2 credentials and endpoint from environment variables
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_ENDPOINT = os.environ.get("R2_ENDPOINT") 

# Configure boto3 client using the environment variables
s3_client = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
)

property_bp = Blueprint('property_bp', __name__)

ALLOWED_LABELS = {
    "main", "bathroom", "bedroom", "kitchen",
    "living_room", "balcony", "closet", "amenities"
}

# ----------------------------------------
# GET All Properties
# ----------------------------------------
from sqlalchemy.orm import joinedload  # optional: for eager loading

@property_bp.route("/properties", methods=["GET"])
@pre_authorized_cors_preflight
def get_all_properties():
    print("[GET] Request to fetch all properties.")
    try:
        # Optionally use eager loading to ensure building is loaded:
        properties = db.session.query(Property).options(joinedload(Property.building)).all()
        if not properties:
            print("[GET] No properties found.")
            return jsonify({"message": "No properties found"}), 404

        property_list = []
        for prop in properties:
            property_data = {
                "id": prop.id,
                "property_code": prop.property_code,
                "building": prop.building.name if prop.building else None,
                "building_id": prop.building_id,
                "unit": prop.unit,
                "owner": prop.owner,
                "contact": prop.contact,
                "size": float(prop.size) if prop.size else None,
                "bedrooms": prop.bedrooms,
                "bathrooms": prop.bathrooms,
                "year_built": prop.year_built,
                "floor": prop.floor,
                "area": prop.area,
                "status": prop.status,
                "price": float(prop.price) if prop.price else None,
                "sell_price": float(prop.sell_price) if prop.sell_price else None,
                "sent": prop.sent,
                "preferred_tenant": prop.preferred_tenant,
                "photo_urls": prop.get_photo_urls(),
                "created_at": prop.created_at.strftime('%Y-%m-%d %H:%M:%S') if prop.created_at else None,
            }
            property_list.append(property_data)
        
        # Log the complete data before returning it
        print("[GET] Returning list of properties:")
        for p in property_list:
            print(p)
        
        return jsonify(property_list), 200

    except Exception as e:
        print(f"[GET] Exception: {str(e)}")
        return jsonify({"error": f"Failed to fetch properties: {str(e)}"}), 500
# ----------------------------------------
# GET Property by ID
# ----------------------------------------
@property_bp.route("/properties/<int:property_id>", methods=["GET"])
@pre_authorized_cors_preflight
def get_property(property_id):
    try:
        prop = (
            db.session.query(Property)
            .options(joinedload(Property.building))
            .filter(Property.id == property_id)
            .first()
        )
        if not prop:
            return jsonify({"error": "Property not found"}), 404

        property_data = {
            "id": prop.id,
            "property_code": prop.property_code,
            "building": prop.building.name if prop.building else None,
            "building_id": prop.building_id,
            "unit": prop.unit,
            "owner": prop.owner,
            "contact": prop.contact,
            "size": float(prop.size) if prop.size else None,
            "bedrooms": prop.bedrooms,
            "bathrooms": prop.bathrooms,
            "year_built": prop.year_built,
            "floor": prop.floor,
            "area": prop.area,
            "status": prop.status,
            "price": float(prop.price) if prop.price else None,
            "sell_price": float(prop.sell_price) if prop.sell_price else None,
            "sent": prop.sent,
            "preferred_tenant": prop.preferred_tenant,
            "photo_urls": prop.get_photo_urls(),
            "created_at": prop.created_at.strftime('%Y-%m-%d %H:%M:%S') if prop.created_at else None,
        }
        return jsonify(property_data), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch property: {str(e)}"}), 500

# ----------------------------------------
# CREATE a New Property
# ----------------------------------------
@property_bp.route("/properties", methods=["POST"])
@pre_authorized_cors_preflight
def create_property():
    data = request.get_json()
    print("[POST] Attempting to create a new property.")
    print(f"[POST] Received data: {data}")

    try:
        new_property = Property(
            property_code=data.get("property_code"),
            building_id=data.get("building_id"),  # using building_id now
            unit=data.get("unit"),
            owner=data.get("owner"),
            contact=data.get("contact"),
            size=float(data["size"]) if data.get("size") else None,
            bedrooms=int(data["bedrooms"]) if data.get("bedrooms") else None,
            bathrooms=int(data["bathrooms"]) if data.get("bathrooms") else None,
            year_built=int(data["year_built"]) if data.get("year_built") else None,
            floor=int(data["floor"]) if data.get("floor") else None,
            area=data.get("area"),
            status=data.get("status"),
            price=float(data["price"]) if data.get("price") else None,
            sell_price=float(data["sell_price"]) if data.get("sell_price") else None,
            sent=data.get("sent"),
            preferred_tenant=data.get("preferred_tenant"),
            photo_urls=data.get("photo_urls")
        )

        db.session.add(new_property)
        db.session.commit()

        print(f"[POST] Property created successfully with ID: {new_property.id}")
        return jsonify({"message": "Property created successfully", "property_id": new_property.id}), 201

    except Exception as e:
        db.session.rollback()
        print(f"[POST] Exception occurred while creating property: {str(e)}")
        return jsonify({"error": f"Failed to create property: {str(e)}"}), 500

# ----------------------------------------
# UPDATE a Property
# ----------------------------------------
@property_bp.route("/properties/<int:property_id>", methods=["PUT"])
@pre_authorized_cors_preflight
def update_property(property_id):
    print(f"[PUT] Request to update property ID: {property_id}")
    prop = db.session.query(Property).filter(Property.id == property_id).first()
    if not prop:
        print("[PUT] Property not found!")
        return jsonify({"error": "Property not found"}), 404

    data = request.get_json()
    print(f"[PUT] Received update data: {data}")

    try:
        prop.property_code = data.get("property_code", prop.property_code)
        prop.building_id = data.get("building_id", prop.building_id)  # update building via building_id
        prop.unit = data.get("unit", prop.unit)
        prop.owner = data.get("owner", prop.owner)
        prop.contact = data.get("contact", prop.contact)
        prop.size = float(data["size"]) if data.get("size") else prop.size
        prop.bedrooms = int(data["bedrooms"]) if data.get("bedrooms") else prop.bedrooms
        prop.bathrooms = int(data["bathrooms"]) if data.get("bathrooms") else prop.bathrooms
        prop.year_built = int(data["year_built"]) if data.get("year_built") else prop.year_built
        prop.floor = int(data["floor"]) if data.get("floor") else prop.floor
        prop.area = data.get("area", prop.area)
        prop.status = data.get("status", prop.status)
        prop.price = float(data["price"]) if data.get("price") else prop.price
        prop.sell_price = float(data["sell_price"]) if data.get("sell_price") else prop.sell_price
        prop.sent = data.get("sent", prop.sent)
        prop.preferred_tenant = data.get("preferred_tenant", prop.preferred_tenant)

        if data.get("photo_urls") is not None:
            prop.photo_urls = data.get("photo_urls")

        db.session.commit()
        print("[PUT] Property updated successfully.")
        return jsonify({"message": "Property updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[PUT] Exception occurred while updating property: {str(e)}")
        return jsonify({"error": f"Failed to update property: {str(e)}"}), 500

# ----------------------------------------
# DELETE a Property
# ----------------------------------------
@property_bp.route("/properties/<int:property_id>", methods=["DELETE"])
@pre_authorized_cors_preflight
def delete_property(property_id):
    print(f"[DELETE] Request to delete property ID: {property_id}")
    prop = db.session.query(Property).filter(Property.id == property_id).first()
    if not prop:
        print("[DELETE] Property not found!")
        return jsonify({"error": "Property not found"}), 404

    try:
        db.session.delete(prop)
        db.session.commit()
        print(f"[DELETE] Property ID {property_id} deleted successfully.")
        return jsonify({"message": "Property deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[DELETE] Exception occurred while deleting property: {str(e)}")
        return jsonify({"error": f"Failed to delete property: {str(e)}"}), 500

# ----------------------------------------
# UPLOAD NEW PROPERTY PHOTO WITH LABEL
# ----------------------------------------
@property_bp.route("/upload", methods=["POST"])
@pre_authorized_cors_preflight
def upload_photo():
    print("[UPLOAD DEBUG] Request files:", request.files)
    if "file" not in request.files:
        print("[UPLOAD DEBUG] No file part in the request")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        print("[UPLOAD DEBUG] No selected file")
        return jsonify({"error": "No selected file"}), 400

    label = request.form.get("label")
    print(f"[UPLOAD DEBUG] Received label: {label}")

    if not label or label not in ALLOWED_LABELS:
        error_message = f"Invalid label provided. Allowed labels: {', '.join(ALLOWED_LABELS)}"
        print(f"[UPLOAD DEBUG] {error_message}")
        return jsonify({"error": error_message}), 400

    bucket_name = "amasproperties"
    filename = f"{uuid.uuid4()}_{file.filename}"
    print(f"[UPLOAD DEBUG] Generated filename: {filename}")

    try:
        s3_client.upload_fileobj(
            file,
            bucket_name,
            filename,
            ExtraArgs={"ACL": "public-read", "ContentType": file.content_type}
        )
        endpoint_hostname = R2_ENDPOINT.replace("https://", "")
        file_url = f"https://{bucket_name}.{endpoint_hostname}/{filename}"
        print(f"[UPLOAD DEBUG] File successfully uploaded: {file_url}")
        return jsonify({"url": f"{R2_ENDPOINT}/{filename}", "label": label}), 200
    except Exception as e:
        print(f"[UPLOAD DEBUG] Error during upload: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ----------------------------------------
# UPLOAD BULK PROPERTY 
# ----------------------------------------
@property_bp.route("/properties/bulk", methods=["POST"])
@pre_authorized_cors_preflight
def bulk_create_properties():
    data = request.get_json()
    if not data or not isinstance(data, list):
        print("[BULK UPLOAD] Invalid input: expecting a list of properties.")
        return jsonify({"error": "Invalid input, expecting a list of properties"}), 400

    created_count = 0
    skipped_count = 0
    total = len(data)
    print(f"[BULK UPLOAD] Received {total} properties to process.")

    for idx, prop in enumerate(data, start=1):
        property_code = prop.get("property_code")
        if property_code:
            # Remove any extraneous whitespace
            property_code = property_code.strip()
        else:
            print(f"[BULK UPLOAD] Property at index {idx} missing property_code. Skipping.")
            skipped_count += 1
            continue

        print(f"[BULK UPLOAD] Processing property {idx}/{total}: Code={property_code}")

        existing_property = db.session.query(Property).filter(Property.property_code == property_code).first()
        if existing_property:
            print(f"[BULK UPLOAD] Skipping property {property_code}: Duplicate found.")
            skipped_count += 1
            continue

        try:
            # Retrieve building info from the payload
            building_name = prop.get("building")
            building_id = prop.get("building_id")  # Optional, provided if available

            # If no building_id is provided but we have a building name, try to look it up or create a new one
            if not building_id and building_name:
                building_name = building_name.strip()
                building = db.session.query(Building).filter(Building.name == building_name).first()
                if building:
                    building_id = building.id
                    print(f"[BULK UPLOAD] Found existing building '{building_name}' with id {building_id}.")
                else:
                    # Create new building record
                    building = Building(name=building_name)
                    db.session.add(building)
                    db.session.flush()  # Flush to get the new building's ID without committing
                    building_id = building.id
                    print(f"[BULK UPLOAD] Created new building '{building_name}' with id {building_id}.")

            # You can choose to either enforce that every property must have a building id
            # or allow it to be None. Here, we assume it's required.
            if not building_id:
                print(f"[BULK UPLOAD] Property {property_code} has no building id and no building name. Skipping.")
                skipped_count += 1
                continue

            new_property = Property(
                property_code=property_code,
                building_id=building_id,
                building_name=building_name,  # Directly store the provided building name
                unit=prop.get("unit"),
                owner=prop.get("owner"),
                contact=prop.get("contact"),
                size=float(prop["size"]) if prop.get("size") else None,
                bedrooms=int(prop["bedrooms"]) if prop.get("bedrooms") else None,
                bathrooms=int(prop["bathrooms"]) if prop.get("bathrooms") else None,
                year_built=int(prop["year_built"]) if prop.get("year_built") else None,
                floor=int(prop["floor"]) if prop.get("floor") else None,
                area=prop.get("area"),
                status=prop.get("status"),
                price=float(prop["price"]) if prop.get("price") else None,
                sell_price=float(prop["sell_price"]) if prop.get("sell_price") else None,
                sent=prop.get("sent"),
                preferred_tenant=prop.get("preferred_tenant"),
                photo_urls=prop.get("photo_urls") or {
                    "main": [f"{R2_ENDPOINT}/noimageyet.jpg"]
                }
            )
            db.session.add(new_property)
            created_count += 1
            print(f"[BULK UPLOAD] Added property {property_code} for insertion.")
        except Exception as e:
            print(f"[BULK UPLOAD] Error processing property {property_code}: {str(e)}")
            skipped_count += 1
            continue

    try:
        db.session.commit()
        print(f"[BULK UPLOAD] Commit successful: {created_count} created, {skipped_count} skipped.")
        return jsonify({
            "message": f"{created_count} properties created successfully, {skipped_count} properties skipped due to duplicate or missing data"
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[BULK UPLOAD] Commit failed: {str(e)}")
        return jsonify({"error": f"Failed to create properties: {str(e)}"}), 500
