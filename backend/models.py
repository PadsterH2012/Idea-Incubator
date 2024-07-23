from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Explicitly set the table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    projects = db.relationship('Project', backref='user', lazy=True)
    provider_settings = db.relationship('ProviderSettings', backref='user', lazy=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Project {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class ProviderSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider_name = db.Column(db.String(50), nullable=False)
    ollama_url = db.Column(db.String(200), nullable=True)
    models = db.Column(db.Text, nullable=True)  # Store as JSON string

    def __repr__(self):
        return f'<ProviderSettings {self.provider_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'provider_name': self.provider_name,
            'ollama_url': self.ollama_url,
            'models': self.models
        }

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    provider = db.Column(db.String(50), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    system_prompt = db.Column(db.Text, nullable=True)
    web_search = db.Column(db.Boolean, default=False)
    temperature = db.Column(db.Float, default=0.7)

    def __repr__(self):
        return f'<Role {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'provider': self.provider,
            'model': self.model,
            'system_prompt': self.system_prompt,
            'web_search': self.web_search,
            'temperature': self.temperature
        }
