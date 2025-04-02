import random
import string
from flask import Blueprint, request, jsonify
from models.sql_models import Client, Property, ClientProperty
from database import db
from datetime import datetime
from helpers.cors_helpers import pre_authorized_cors_preflight

client_bp = Blueprint("client_bp", __name__)

def generate_random_access_key():
    # Generates a random 6-character alphanumeric string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ----------------------------------------
# 1. GET Client Details by ID (including assigned properties and login details)
# ----------------------------------------
@client_bp.route("/clients/<int:client_id>", methods=["GET"])
@pre_authorized_cors_preflight
def get_client(client_id):
    print(f"[GET] Fetching client with ID: {client_id}")
    client = db.session.query(Client).filter(Client.id == client_id).first()
    if not client:
        print("[GET] Client not found!")
        return jsonify({"error": "Client not found"}), 404
    print(f"[GET] Client found: {client}")
    
    # Build a list of assigned properties including all needed details
    assigned_props = []
    for cp in client.client_properties:
        prop = cp.property
        # Defensive check (in case of orphaned record)
        if not prop:
            continue
        assigned_props.append({
            "id": prop.id,
            "property_code": prop.property_code,
            "building": prop.building.name if prop.building else prop.building_name,
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
            "created_at": cp.created_at.strftime('%Y-%m-%d %H:%M:%S') if cp.created_at else None,
            "comment": cp.comment,
            "is_active": cp.is_active
        })
    
    # Return client details without the extra 'building' field at the client level
    return jsonify({
        "id": client.id,
        "code": client.code,
        "title": client.title,
        "first_name": client.first_name,
        "last_name": client.last_name,
        "nationality": client.nationality,
        "contact_type": client.contact_type,
        "contact": client.contact,
        "starting_date": client.starting_date.strftime('%Y-%m-%d') if client.starting_date else None,
        "move_in": client.move_in.strftime('%Y-%m-%d') if client.move_in else None,
        "budget": float(client.budget) if client.budget else None,
        "bedrooms": client.bedrooms,
        "bath": client.bath,
        "area": client.area,
        "size": float(client.size) if client.size else None,
        "preferred": client.preferred,
        "status": client.status,
        "work_sheet": client.work_sheet,
        "login_link": client.login_link,
        "access_key": client.access_key,
        "assigned_properties": assigned_props
    })


# ----------------------------------------
# 2. UPDATE Client Details
# ----------------------------------------
@client_bp.route("/clients/<int:client_id>", methods=["PUT"])
@pre_authorized_cors_preflight
def update_client(client_id):
    print(f"[PUT] Updating client ID: {client_id}")
    client = db.session.query(Client).filter(Client.id == client_id).first()
    if not client:
        print("[PUT] Client not found!")
        return jsonify({"error": "Client not found"}), 404

    data = request.get_json()
    print(f"[PUT] Received data: {data}")

    try:
        client.title = data.get("title", client.title)
        client.first_name = data.get("first_name", client.first_name)
        client.last_name = data.get("last_name", client.last_name)
        client.nationality = data.get("nationality", client.nationality)
        client.contact_type = data.get("contact_type", client.contact_type)
        client.contact = data.get("contact", client.contact)

        if "starting_date" in data:
            client.starting_date = datetime.strptime(data["starting_date"], "%Y-%m-%d") if data["starting_date"] else None
        if "move_in" in data:
            client.move_in = datetime.strptime(data["move_in"], "%Y-%m-%d") if data["move_in"] else None
        client.budget = data.get("budget", client.budget)
        client.bedrooms = data.get("bedrooms", client.bedrooms)
        client.bath = data.get("bath", client.bath)
        client.area = data.get("area", client.area)
        client.size = data.get("size", client.size)
        client.preferred = data.get("preferred", client.preferred)
        client.status = data.get("status", client.status)
        client.work_sheet = data.get("work_sheet", client.work_sheet)

        normalized_code = client.code.strip().upper()
        client.code = normalized_code  # Ensure code is uppercase

        # Always generate a new random access key
        client.access_key = generate_random_access_key()
        client.login_link = f"https://amascrm.netlify.app/client-portal/{normalized_code}"

        db.session.commit()
        print("[PUT] Client updated successfully!")
        return jsonify({"message": "Client updated successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"[PUT] Error updating client: {e}")
        return jsonify({"error": f"Failed to update client: {str(e)}"}), 500

# ----------------------------------------
# 3. CREATE a New Client
# ----------------------------------------
@client_bp.route("/clients", methods=["POST"])
@pre_authorized_cors_preflight
def create_client():
    data = request.get_json()
    print(f"[POST] Creating new client with data: {data}")

    try:
        normalized_code = data.get("code", "").strip().upper()
        contact = data.get("contact", "").strip()
        
        computed_login_link = f"https://amascrm.netlify.app/client-portal/{normalized_code}"
        computed_access_key = generate_random_access_key()

        new_client = Client(
            code=normalized_code,
            title=data.get("title") or None,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            nationality=data.get("nationality") or None,
            contact_type=data.get("contact_type") or None,
            contact=contact,  # Now required in the model
            starting_date=datetime.strptime(data["starting_date"], "%Y-%m-%d") if data.get("starting_date") else None,
            move_in=datetime.strptime(data["move_in"], "%Y-%m-%d") if data.get("move_in") else None,
            budget=float(data["budget"]) if data.get("budget") else None,
            bedrooms=int(data["bedrooms"]) if data.get("bedrooms") else None,
            bath=int(data["bath"]) if data.get("bath") else None,
            area=data.get("area") or None,
            preferred=data.get("preferred") or None,
            status=data.get("status") or None,
            work_sheet=data.get("work_sheet") or None,
            login_link=computed_login_link,
            access_key=computed_access_key,
        )

        db.session.add(new_client)
        db.session.commit()
        return jsonify({"message": "Client created successfully", "client_id": new_client.id}), 201
    except Exception as e:
        db.session.rollback()
        print(f"[POST] Error creating client: {e}")
        return jsonify({"error": f"Failed to create client: {str(e)}"}), 500

# ----------------------------------------
# 4. DELETE a Client
# ----------------------------------------
@client_bp.route("/clients/<int:client_id>", methods=["DELETE"])
@pre_authorized_cors_preflight
def delete_client(client_id):
    print(f"[DELETE] Deleting client ID: {client_id}")
    client = db.session.query(Client).filter(Client.id == client_id).first()
    if not client:
        print("[DELETE] Client not found!")
        return jsonify({"error": "Client not found"}), 404

    try:
        db.session.delete(client)
        db.session.commit()
        print("[DELETE] Client deleted successfully!")
        return jsonify({"message": "Client deleted successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"[DELETE] Error deleting client: {e}")
        return jsonify({"error": f"Failed to delete client: {str(e)}"}), 500

# ----------------------------------------
# 5. GET All Clients
# ----------------------------------------
@client_bp.route("/clients", methods=["GET"])
@pre_authorized_cors_preflight
def get_all_clients():
    print("[GET] Fetching all clients...")
    try:
        clients = db.session.query(Client).all()
        if not clients:
            print("[GET] No clients found!")
            return jsonify({"message": "No clients found"}), 404

        client_list = []
        for client in clients:
            client_data = {
                "id": client.id,
                "code": client.code,
                "title": client.title,
                "first_name": client.first_name,
                "last_name": client.last_name,
                "nationality": client.nationality,
                "contact_type": client.contact_type,
                "contact": client.contact,
                "starting_date": client.starting_date.strftime('%Y-%m-%d') if client.starting_date else None,
                "move_in": client.move_in.strftime('%Y-%m-%d') if client.move_in else None,
                "budget": float(client.budget) if client.budget else None,
                "bedrooms": client.bedrooms,
                "bath": client.bath,
                "area": client.area,
                "preferred": client.preferred,
                "status": client.status,
                "work_sheet": client.work_sheet
            }
            client_list.append(client_data)
        print(f"[GET] Found {len(client_list)} clients.")
        return jsonify(client_list), 200
    except Exception as e:
        print(f"[GET] Error fetching clients: {e}")
        return jsonify({"error": f"Failed to fetch clients: {str(e)}"}), 500

# ----------------------------------------
# 6. ADD/REMOVE Assigned Property
# ----------------------------------------
@client_bp.route("/clients/<int:client_id>/properties", methods=["POST"])
@pre_authorized_cors_preflight
def add_property_to_client(client_id):
    from models.sql_models import Property, ClientProperty
    data = request.get_json()
    property_id = data.get("property_id")
    print(f"[POST] Assign property {property_id} to client {client_id}")
    if not property_id:
        return jsonify({"error": "property_id is required"}), 400
    client = db.session.query(Client).filter_by(id=client_id).first()
    if not client:
        return jsonify({"error": "Client not found"}), 404
    prop = db.session.query(Property).filter_by(id=property_id).first()
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    existing_link = db.session.query(ClientProperty).filter_by(client_id=client.id, property_id=prop.id).first()
    if existing_link:
        print("[POST] Property already assigned.")
        return jsonify({"message": "Property already assigned"}), 200
    # New assignments default to inactive (is_active=False)
    new_link = ClientProperty(client_id=client.id, property_id=prop.id, is_active=False)
    db.session.add(new_link)
    db.session.commit()
    return jsonify({"message": "Property assigned successfully"}), 201

@client_bp.route("/clients/<int:client_id>/properties/<int:property_id>", methods=["DELETE"])
@pre_authorized_cors_preflight
def remove_property_from_client(client_id, property_id):
    from models.sql_models import ClientProperty
    print(f"[DELETE] Remove property {property_id} from client {client_id}")
    link = db.session.query(ClientProperty).filter_by(client_id=client_id, property_id=property_id).first()
    if not link:
        return jsonify({"error": "Link not found"}), 404
    db.session.delete(link)
    db.session.commit()
    print("[DELETE] Link removed successfully.")
    return jsonify({"message": "Property removed from client"}), 200

# ----------------------------------------
# 7. GET Client Details by Code
# ----------------------------------------
@client_bp.route("/clients/code/<string:client_code>", methods=["GET"])
@pre_authorized_cors_preflight
def get_client_by_code(client_code):
    print(f"[GET] Fetching client with code: {client_code}")
    client = db.session.query(Client).filter(Client.code == client_code).first()
    if not client:
        print("[GET] Client not found!")
        return jsonify({"error": "Client not found"}), 404
    assigned_props = []
    for cp in client.client_properties:
        prop = cp.property
        print(f"[DEBUG] Property ID: {prop.id}, Building: {prop.building}, Unit: {prop.unit}, Size: {prop.size}, Year Built: {prop.year_built}")
        assigned_props.append({
            "id": prop.id,
            "property_code": prop.property_code,
            "building": prop.building.name if prop.building else prop.building_name,
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
            "created_at": cp.created_at.strftime('%Y-%m-%d %H:%M:%S') if cp.created_at else None,
            "comment": cp.comment,
            "is_active": cp.is_active
        })
    return jsonify({
        "id": client.id,
        "code": client.code,
        "building": client.client_properties[-1].property.building.name if client.client_properties and client.client_properties[-1].property.building else None,
        "title": client.title,
        "first_name": client.first_name,
        "last_name": client.last_name,
        "nationality": client.nationality,
        "contact_type": client.contact_type,
        "contact": client.contact,
        "starting_date": client.starting_date.strftime('%Y-%m-%d') if client.starting_date else None,
        "move_in": client.move_in.strftime('%Y-%m-%d') if client.move_in else None,
        "budget": float(client.budget) if client.budget else None,
        "bedrooms": client.bedrooms,
        "bath": client.bath,
        "area": client.area,
        "size": float(client.size) if client.size else None,  # NEW: include size here
        "preferred": client.preferred,
        "status": client.status,
        "work_sheet": client.work_sheet,
        "assigned_properties": assigned_props
    })
# ----------------------------------------
# 8. Generate Login Details (Recalculate access key and login link)
# ----------------------------------------
@client_bp.route("/clients/<int:client_id>/generate_login", methods=["PUT"])
@pre_authorized_cors_preflight
def generate_login_details(client_id):
    print(f"[PUT] Generating login details for client ID: {client_id}")
    client = db.session.query(Client).filter(Client.id == client_id).first()
    if not client:
        print("[PUT] Client not found!")
        return jsonify({"error": "Client not found"}), 404
    try:
        normalized_code = client.code.strip().upper()
        client.code = normalized_code
        client.access_key = generate_random_access_key()
        client.login_link = f"https://amascrm.netlify.app/client-portal/{normalized_code}"
        db.session.commit()
        return jsonify({
            "message": "Login details generated successfully",
            "login_link": client.login_link,
            "access_key": client.access_key
        })
    except Exception as e:
        db.session.rollback()
        print(f"[PUT] Error generating login details: {e}")
        return jsonify({"error": f"Failed to generate login details: {str(e)}"}), 500

# ----------------------------------------
# 9. UPDATE Client Property Comment and Active Status
# ----------------------------------------
@client_bp.route("/clients/<int:client_id>/properties/<int:property_id>/comment", methods=["PUT"])
@pre_authorized_cors_preflight
def update_client_property_comment(client_id, property_id):
    data = request.get_json()
    print("[DEBUG] Received data:", data)  # Debug: show entire payload

    # Check that at least one of 'comment' or 'is_active' is provided.
    if "comment" not in data and "is_active" not in data:
        print("[DEBUG] Neither 'comment' nor 'is_active' provided in request data")
        return jsonify({"error": "At least one of 'comment' or 'is_active' is required"}), 400

    # Retrieve the client property assignment
    client_property = db.session.query(ClientProperty).filter_by(
        client_id=client_id, property_id=property_id
    ).first()
    if not client_property:
        print(f"[DEBUG] No client property assignment found for client_id: {client_id} and property_id: {property_id}")
        return jsonify({"error": "Client property assignment not found"}), 404

    # Update the comment if provided
    if "comment" in data:
        new_comment = data.get("comment")
        print(f"[DEBUG] New comment: {new_comment}")
        client_property.comment = new_comment

    # Update is_active if provided
    if "is_active" in data:
        try:
            is_active_value = bool(data["is_active"])
            print(f"[DEBUG] Updating is_active to: {is_active_value}")
            client_property.is_active = is_active_value
        except Exception as e:
            print(f"[DEBUG] Error converting is_active value: {e}")
            return jsonify({"error": "Invalid value for is_active"}), 400

    try:
        db.session.commit()
        print("[DEBUG] Client property updated successfully")
        return jsonify({"message": "Client property updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"[DEBUG] Exception during commit: {e}")
        return jsonify({"error": f"Failed to update client property: {str(e)}"}), 500