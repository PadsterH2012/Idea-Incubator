from flask import jsonify, session, render_template, url_for, request, redirect, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from models import User, Project, ProviderSettings, Role
from app import app, db
from flask_login import login_user, login_required, logout_user, current_user
from functools import wraps
import json

# Move the login_required decorator definition here
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            app.logger.warning("User not in session, redirecting to index")
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'message': 'Unauthorized'}), 401
            return redirect(url_for('index', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/project/<int:project_id>/interact')
@login_required
def project_interaction(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_interaction.html', project=project)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            app.logger.warning("User not in session, redirecting to index")
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'message': 'Unauthorized'}), 401
            return redirect(url_for('index', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['POST'])
def register():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    if not data or 'username' not in data or 'email' not in data or 'password' not in data:
        return jsonify({'message': 'Missing username, email, or password'}), 400
    
    username = data['username']
    email = data['email']
    password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    
    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully!'})

@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'message': 'Missing username or password'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if user and check_password_hash(user.password, data['password']):
            login_user(user)
            session['user_id'] = user.id  # Explicitly set user_id in session
            app.logger.info(f"User {user.id} logged in successfully")
            app.logger.info(f"Session after login: {session}")
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('dashboard')
            return jsonify({'message': 'Login successful!', 'redirect': next_page})
        
        app.logger.warning(f"Failed login attempt for username: {data['username']}")
        return jsonify({'message': 'Invalid credentials!'}), 401
    
    return render_template('index.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully!'})

@app.route('/login')
def login_page():
    return redirect(url_for('index'))

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    app.logger.info(f"Accessing dashboard. User ID in session: {session.get('user_id')}")
    app.logger.info(f"Current user: {current_user}")
    return render_template('dashboard.html', username=current_user.username)

@app.route('/user_settings', methods=['GET', 'POST'])
def user_settings():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        data = request.form
        if 'username' in data and 'email' in data and 'currentPassword' in data:
            if check_password_hash(user.password, data['currentPassword']):
                user.username = data['username']
                user.email = data['email']
                db.session.commit()
                return jsonify({'message': 'Profile updated successfully!'})
            else:
                return jsonify({'message': 'Current password is incorrect'}), 400
        else:
            return jsonify({'message': 'Missing required fields'}), 400
    
    return render_template('user_settings.html', username=user.username, email=user.email)

@app.route('/app_settings', methods=['GET', 'POST'])
def app_settings():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        theme = request.form.get('theme')
        session['theme'] = theme
        return jsonify({'message': 'Settings updated successfully!'})
    
    current_theme = session.get('theme', 'light')
    return render_template('app_settings.html', current_theme=current_theme)

@app.route('/provider_settings', methods=['GET', 'POST'])
@login_required
def provider_settings():
    user_id = session['user_id']
    provider_settings = ProviderSettings.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        provider_name = request.form.get('provider_name')
        ollama_url = request.form.get('ollama_url')
        models = request.form.get('models')

        if provider_settings:
            provider_settings.provider_name = provider_name
            provider_settings.ollama_url = ollama_url
            provider_settings.models = models
        else:
            new_settings = ProviderSettings(user_id=user_id, provider_name=provider_name, ollama_url=ollama_url, models=models)
            db.session.add(new_settings)

        db.session.commit()
        return jsonify({'message': 'Provider settings updated successfully!'})

    providers = ['Ollama']  # Add more providers here as needed
    return render_template('provider_settings.html', 
                           provider_settings=provider_settings, 
                           providers=providers)

@app.route('/agents_settings', methods=['GET', 'POST'])
@login_required
def agents_settings():
    # Placeholder for agents settings logic
    return render_template('agents_settings.html')

@app.route('/roles_settings', methods=['GET', 'POST'])
@login_required
def roles_settings():
    user_id = session['user_id']
    provider_settings = ProviderSettings.query.filter_by(user_id=user_id).first()
    
    if request.method == 'POST':
        role_id = request.form.get('role_id')
        role = Role.query.get(role_id)
        if role:
            role.provider = request.form.get('provider')
            role.model = request.form.get('model')
            role.system_prompt = request.form.get('system_prompt')
            role.web_search = 'web_search' in request.form
            role.temperature = float(request.form.get('temperature', 0.7))
            db.session.commit()
            return jsonify({'message': 'Role updated successfully!'})
        return jsonify({'message': 'Role not found'}), 404

    roles = Role.query.all()
    providers = [provider_settings.provider_name] if provider_settings else []
    models = provider_settings.models.split(',') if provider_settings and provider_settings.models else []
    
    return render_template('roles_settings.html', roles=roles, providers=providers, models=models)

from role_prompts import ROLE_PROMPTS

@app.route('/initialize_roles', methods=['POST'])
@login_required
def initialize_roles():
    for role_name, role_data in ROLE_PROMPTS.items():
        existing_role = Role.query.filter_by(name=role_name).first()
        if existing_role:
            existing_role.system_prompt = role_data['prompt']
            existing_role.temperature = role_data['temperature']
        else:
            new_role = Role(name=role_name, system_prompt=role_data['prompt'], temperature=role_data['temperature'])
            db.session.add(new_role)
    
    db.session.commit()
    return jsonify({'message': 'Roles initialized successfully!'})

@app.route('/projects')
@login_required
def projects_page():
    app.logger.info(f"Session: {session}")
    app.logger.info(f"Request headers: {request.headers}")
    app.logger.info(f"Request cookies: {request.cookies}")
    
    app.logger.info(f"User {session['user_id']} accessing projects page")
    
    user = User.query.get(session['user_id'])
    projects = Project.query.filter_by(user_id=session['user_id']).all()
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'projects': [project.to_dict() for project in projects]})
    else:
        return render_template('projects.html', username=user.username, projects=projects)

@app.after_request
def after_request(response):
    app.logger.info(f"After request - Session: {session}")
    app.logger.info(f"After request - Response headers: {response.headers}")
    return response

@app.route('/projects', methods=['GET'])
def get_projects():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    user_id = session['user_id']
    projects = Project.query.filter_by(user_id=user_id).all()
    app.logger.info(f"User ID: {user_id}, Number of projects: {len(projects)}")
    for project in projects:
        app.logger.info(f"Project ID: {project.id}, Name: {project.name}")
    return jsonify({'projects': [project.to_dict() for project in projects]})

@app.route('/project', methods=['POST'])
def create_project():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    data = request.json
    new_project = Project(name=data['name'], description=data['description'], user_id=session['user_id'])
    db.session.add(new_project)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Project created successfully'})

@app.route('/project/<int:project_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if not project:
        return jsonify({'message': 'Project not found'}), 404

    if request.method == 'GET':
        # Fetch the AI Agent Project Planner role
        planner_role = Role.query.filter_by(name='AI Agent Project Planner').first()
        
        return render_template('project_interaction.html', project=project, planner_role=planner_role)
    
    elif request.method == 'PUT':
        data = request.json
        project.name = data['name']
        project.description = data['description']
        db.session.commit()
        return jsonify({'success': True, 'message': 'Project updated successfully'})
    
    elif request.method == 'DELETE':
        db.session.delete(project)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Project deleted successfully'})
    
@app.route('/api/project/<int:project_id>/details', methods=['GET'])
@login_required
def get_project_details(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Fetch the "AI Agent - Project Planner" role
    planner_role = Role.query.filter_by(name="AI Agent - Project Planner").first()
    
    if not planner_role:
        return jsonify({"error": "AI Agent - Project Planner role not found"}), 404
    
    # Fetch the ProviderSettings for the current user
    provider_settings = ProviderSettings.query.filter_by(user_id=current_user.id).first()
    
    if not provider_settings:
        return jsonify({"error": "Provider settings not found"}), 404
    
    return jsonify({
        "api_url": provider_settings.ollama_url or "Not set",
        "model_name": planner_role.model or "Not set",
        "role_name": planner_role.name,
        "role_provider": planner_role.provider or "Not set",
        "role_model": planner_role.model or "Not set",
        "role_system_prompt": planner_role.system_prompt or "Not set",
        "role_web_search": "Enabled" if planner_role.web_search else "Disabled",
        "role_temperature": planner_role.temperature or "Not set"
    })
