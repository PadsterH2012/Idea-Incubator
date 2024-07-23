# Idea Incubator

Idea Incubator is a web application designed to help users capture, develop, and track their innovative ideas. Built with Flask and PostgreSQL, this application provides a robust platform for idea management and collaboration.

## Features

- User authentication system (registration, login, logout)
- Project creation and management
- User dashboard for project overview
- User and application settings
- Responsive design with light/dark mode
- RESTful API structure
- Docker containerization for easy deployment

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/idea-incubator.git
   cd idea-incubator
   ```

2. Build and run the Docker containers:
   ```
   docker-compose up --build
   ```

3. Access the application at `http://localhost:5000`

## Project Structure

```
idea-incubator/
├── backend/
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── dashboard.html
│   │   ├── user_settings.html
│   │   ├── app_settings.html
│   │   └── projects.html
│   ├── static/
│   │   └── css/
│   │       ├── base.css
│   │       ├── dark-theme.css
│   │       └── projects.css
│   ├── app.py
│   ├── routes.py
│   ├── models.py
│   ├── Dockerfile
│   └── requirements.txt
├── db/
│   └── init.sql
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Usage

1. Visit the homepage and register a new account
2. Log in with your credentials
3. Navigate to the Projects page to create and manage your projects
4. Use the dashboard for an overview of your activities
5. Customize your experience in the user and app settings

## Development

To make changes to the application:

1. Modify the Flask application in `backend/app.py`
2. Update routes in `backend/routes.py`
3. Modify database models in `backend/models.py`
4. Update HTML templates in `backend/templates/`
5. Add or modify CSS in `backend/static/css/`
6. Rebuild and restart the Docker containers to see your changes:
   ```
   docker-compose down
   docker-compose up --build
   ```

## Database Migrations

This project uses Flask-Migrate for database migrations. To create and apply migrations:

1. Access the backend container:
   ```
   docker-compose exec backend bash
   ```

2. Initialize migrations (if not already done):
   ```
   flask db init
   ```

3. Create a new migration:
   ```
   flask db migrate -m "Description of changes"
   ```

4. Apply the migration:
   ```
   flask db upgrade
   ```

### Recent Database Changes

A new `temperature` column has been added to the `Role` model. This column stores a float value with a default of 0.7. The migration script `add_temperature_to_role.py` has been created to handle this change.

To apply this change to your database:

1. Ensure you're in the backend container:
   ```
   docker-compose exec backend bash
   ```

2. Run the database upgrade:
   ```
   flask db upgrade
   ```

If you encounter any issues with the migration, the application will attempt to add the column manually during startup.

## API Endpoints

- POST `/register`: Register a new user
- POST `/login`: Authenticate a user
- POST `/logout`: Log out the current user
- GET `/dashboard`: Access user dashboard
- GET, POST `/user_settings`: View and update user settings
- GET, POST `/app_settings`: View and update application settings
- GET `/projects`: View all projects
- POST `/project`: Create a new project
- GET, PUT, DELETE `/project/<int:project_id>`: View, update, or delete a specific project

## Security Features

- Password hashing using Werkzeug's generate_password_hash and check_password_hash
- Session-based authentication
- CSRF protection
- Input validation and sanitization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgements

- Flask
- SQLAlchemy
- PostgreSQL
- Docker
- Werkzeug
