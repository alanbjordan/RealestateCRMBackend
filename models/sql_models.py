from datetime import datetime
import json
from database import db, bcrypt

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    user_uuid = db.Column(db.String(36), unique=True, nullable=False)  # <-- New column
    password_hash = db.Column(db.Text, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Hash and set user password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        """Check if provided password matches stored hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"
    
class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(10))
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    nationality = db.Column(db.String(100))
    contact_type = db.Column(db.String(50))
    contact = db.Column(db.String(100), nullable=False)  # Updated: now not nullable
    starting_date = db.Column(db.Date, nullable=True)
    move_in = db.Column(db.Date, nullable=True)
    budget = db.Column(db.Numeric(10, 2))
    bedrooms = db.Column(db.Integer)
    bath = db.Column(db.Integer)
    area = db.Column(db.String(50))
    size = db.Column(db.Numeric(10, 2))
    preferred = db.Column(db.Text)
    status = db.Column(db.String(100))
    work_sheet = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    login_link = db.Column(db.String(255))
    access_key = db.Column(db.String(50))

    client_properties = db.relationship(
        "ClientProperty", back_populates="client", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Client {self.first_name} {self.last_name}>"

class Building(db.Model):
    __tablename__ = "buildings"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    year_built = db.Column(db.Integer, nullable=True)
    nearest_bts = db.Column(db.String(100), nullable=True)
    nearest_mrt = db.Column(db.String(100), nullable=True)
    distance_to_bts = db.Column(db.Numeric(10,2), nullable=True)
    distance_to_mrt = db.Column(db.Numeric(10,2), nullable=True)
    facilities = db.Column(db.JSON, nullable=True)
    photo_urls = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Building {self.name}>"

class Property(db.Model):
    __tablename__ = "properties"

    id = db.Column(db.Integer, primary_key=True)
    property_code = db.Column(db.String(50), unique=True, nullable=False)  # Alphanumeric
    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable=False)
    building_name = db.Column(db.String(255))  # New column for storing the building's name
    unit = db.Column(db.String(50), nullable=False)
    owner = db.Column(db.String(255))
    contact = db.Column(db.String(100))
    size = db.Column(db.Numeric(10, 2))
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    year_built = db.Column(db.Integer)  # Year built
    floor = db.Column(db.Integer)       # Floor level
    area = db.Column(db.String(2))      # Two-letter alpha code
    status = db.Column(db.String(100))
    price = db.Column(db.Numeric(10, 2))      # Rent price
    sell_price = db.Column(db.Numeric(10, 2))   # THB sale price
    preferred_tenant = db.Column(db.Text)
    sent = db.Column(db.String(3), nullable=True)  # Yes or No
    photo_urls = db.Column(db.JSON, nullable=True)  # Store photo URLs as JSON object
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    building = db.relationship("Building", backref=db.backref("properties", lazy=True))
    client_properties = db.relationship(
        "ClientProperty",
        back_populates="property",
        cascade="all, delete-orphan",
    )

    def set_photo_urls(self, urls):
        """Store photo URLs as JSON (dict)."""
        if isinstance(urls, dict):
            self.photo_urls = urls
        else:
            try:
                self.photo_urls = json.loads(urls)
            except Exception:
                self.photo_urls = {}

    def get_photo_urls(self):
        """Retrieve photo_urls as a dictionary."""
        if not self.photo_urls:
            return {}
        if isinstance(self.photo_urls, dict):
            return self.photo_urls
        try:
            return json.loads(self.photo_urls)
        except Exception:
            return {}

    def __repr__(self):
        # Access building name via the relationship if available, or fall back to building_name
        verified_building = self.building.name if self.building else self.building_name or "Unknown"
        return f"<Property {self.property_code} - {verified_building} - {self.unit}>"

    def __repr__(self):
        # Access building name via the relationship
        building_name = self.building.name if self.building else "Unknown"
        return f"<Property {self.property_code} - {building_name} - {self.unit}>"
    
class ClientProperty(db.Model):
    __tablename__ = "client_properties"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False, nullable=False)  # New column

    client = db.relationship("Client", back_populates="client_properties")
    property = db.relationship("Property", back_populates="client_properties")

    def __repr__(self):
        return f"<ClientProperty client_id={self.client_id} property_id={self.property_id} is_active={self.is_active}>"
