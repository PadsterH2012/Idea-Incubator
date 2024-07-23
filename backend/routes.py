from flask import jsonify, session, render_template, url_for, request, redirect, make_response, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from models import User, Project
from database import db
from functools import wraps

def register_routes(app):
    @app.route('/health')
    def health_check():
        try:
            # Check database connection
            db.session.execute('SELECT 1')
            return jsonify({'status': 'healthy'}), 200
        except Exception as e:
            app.logger.error(f"Health check failed: {str(e)}")
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                app.logger.warning("User not in session, redirecting to login")
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({'message': 'Unauthorized'}), 401
                return redirect(url_for('login', next=request.url))
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

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            if not data or 'username' not in data or 'password' not in data:
                return jsonify({'message': 'Missing username or password'}), 400
            
            user = User.query.filter_by(username=data['username']).first()
            
            if user and check_password_hash(user.password, data['password']):
                session.clear()
                session['user_id'] = user.id
                session.permanent = True
                app.logger.info(f"User {user.id} logged in successfully")
                next_page = request.args.get('next')
                if not next_page or urlparse(next_page).netloc != '':
                    next_page = url_for('dashboard')
                response = jsonify({'message': 'Login successful!', 'redirect': next_page})
                response.set_cookie('session', session.sid, httponly=True, secure=True, samesite='Strict')
                return response
            
            app.logger.warning(f"Failed login attempt for username: {data['username']}")
            return jsonify({'message': 'Invalid credentials!'}), 401
        
        return render_template('login.html')

    @app.route('/logout', methods=['POST'])
    def logout():
        session.pop('user_id', None)
        return jsonify({'message': 'Logged out successfully!'})

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/register')
    def register_page():
        return render_template('register.html')

    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session:
            return jsonify({'message': 'Unauthorized'}), 401
        user = User.query.get(session['user_id'])
        return render_template('dashboard.html', username=user.username)

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

    @app.route('/projects')
    @login_required
    def projects_page():
        try:
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
        except Exception as e:
            app.logger.error(f"An error occurred in projects_page: {str(e)}")
            return jsonify({'error': 'An internal server error occurred'}), 500

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
        current_app.logger.info(f"User ID: {user_id}, Number of projects: {len(projects)}")
        for project in projects:
            current_app.logger.info(f"Project ID: {project.id}, Name: {project.name}")
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
    def manage_project(project_id):
        if 'user_id' not in session:
            return jsonify({'message': 'Unauthorized'}), 401
        
        project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
        if not project:
            return jsonify({'message': 'Project not found'}), 404

        if request.method == 'GET':
            return jsonify(project.to_dict())
        
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