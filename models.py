from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class OSImage(db.Model):
    __tablename__ = 'os_images'

    name = db.Column(db.String(50), primary_key=True)
    uuid = db.Column(db.String(36), nullable=False)


class Configuration(db.Model):
    __tablename__ = 'configurations'

    name = db.Column(db.String(50), primary_key=True)
    id   = db.Column(db.String(100), nullable=False)


class VM(db.Model):
    __tablename__ = 'vms'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    openstack_id = db.Column(db.String(36), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    os = db.Column(db.String(50), nullable=False)
    vcpu = db.Column(db.Integer, nullable=False)
    ram = db.Column(db.Integer, nullable=False)
    ssd = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='building')
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', backref='vms')
