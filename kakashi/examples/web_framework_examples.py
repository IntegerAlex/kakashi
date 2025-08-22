"""
Web framework integration examples for mylogs.

This module shows how to integrate mylogs with popular Python web frameworks.
Note: Framework dependencies are optional and only required when using specific integrations.
"""



def fastapi_example():
    """Example of using mylogs with FastAPI."""
    print("=== FastAPI Integration Example ===")
    
    try:
        from fastapi import FastAPI, HTTPException
        from kakashi.integrations.fastapi_integration import setup_fastapi_logging
        from kakashi.core import get_logger
        
        # Create FastAPI app
        app = FastAPI(title="MyLogs FastAPI Example", version="1.0.0")
        
        # Setup mylogs integration
        fastapi_logger = setup_fastapi_logging(
            app, 
            logger_name="fastapi_example",
            log_file="fastapi_example",
            include_middleware=True,
            middleware_config={
                'exclude_paths': ['/health', '/metrics'],
                'include_request_body': False
            }
        )
        
        # Get a custom logger for business logic
        business_logger = get_logger("business", "fastapi_business")
        
        @app.get("/")
        async def root():
            business_logger.info("Root endpoint accessed")
            return {"message": "Hello World", "framework": "FastAPI"}
        
        @app.get("/users/{user_id}")
        async def get_user(user_id: int):
            business_logger.info(f"Fetching user with ID: {user_id}")
            
            if user_id <= 0:
                business_logger.warning(f"Invalid user ID requested: {user_id}")
                raise HTTPException(status_code=400, detail="Invalid user ID")
            
            # Simulate database operation
            fastapi_logger.log_database_operation("SELECT", "users", 0.05)
            
            user_data = {"id": user_id, "name": f"User {user_id}"}
            business_logger.info(f"User data retrieved: {user_data}")
            
            return user_data
        
        @app.post("/login")
        async def login(username: str, password: str):
            # Simulate authentication
            success = username == "admin" and password == "secret"
            
            fastapi_logger.log_authentication_attempt(username, success)
            
            if not success:
                raise HTTPException(status_code=401, detail="Authentication failed")
            
            return {"token": "example-jwt-token", "user": username}
        
        print("FastAPI app configured with mylogs integration")
        print("Run with: uvicorn your_module:app --reload")
        print("Endpoints:")
        print("- GET / ")
        print("- GET /users/{user_id}")
        print("- POST /login")
        
        return app
        
    except ImportError as e:
        print(f"FastAPI not available: {e}")
        print("Install with: pip install kakashi[fastapi]")
        return None


def flask_example():
    """Example of using mylogs with Flask."""
    print("\n=== Flask Integration Example ===")
    
    try:
        from flask import Flask, jsonify, request
        from kakashi.integrations.flask_integration import init_flask_logging, flask_log_route
        from kakashi.core import get_logger
        
        # Create Flask app
        app = Flask(__name__)
        
        # Initialize mylogs integration
        flask_handler = init_flask_logging(
            app,
            logger_name="flask_example",
            log_file="flask_example",
            exclude_paths=['/static', '/health']
        )
        
        # Get a custom logger for business logic
        business_logger = get_logger("business", "flask_business")
        
        @app.route('/')
        def root():
            business_logger.info("Root endpoint accessed")
            return jsonify({"message": "Hello World", "framework": "Flask"})
        
        @app.route('/users/<int:user_id>')
        @flask_log_route("user_operations", "flask_users")
        def get_user(user_id: int):
            business_logger.info(f"Fetching user with ID: {user_id}")
            
            if user_id <= 0:
                business_logger.warning(f"Invalid user ID requested: {user_id}")
                return jsonify({"error": "Invalid user ID"}), 400
            
            # Simulate database operation
            flask_handler.log_database_query(f"SELECT * FROM users WHERE id = {user_id}", 0.03)
            
            user_data = {"id": user_id, "name": f"User {user_id}"}
            business_logger.info(f"User data retrieved: {user_data}")
            
            return jsonify(user_data)
        
        @app.route('/login', methods=['POST'])
        def login():
            data = request.get_json()
            username = data.get('username', '')
            password = data.get('password', '')
            
            # Simulate authentication
            success = username == "admin" and password == "secret"
            
            if success:
                flask_handler.log_user_action("login", username)
                return jsonify({"token": "example-jwt-token", "user": username})
            else:
                business_logger.warning(f"Failed login attempt for: {username}")
                return jsonify({"error": "Authentication failed"}), 401
        
        @app.errorhandler(Exception)
        def handle_error(error):
            business_logger.error(f"Unhandled error: {error}")
            return jsonify({"error": "Internal server error"}), 500
        
        print("Flask app configured with mylogs integration")
        print("Run with: python your_module.py")
        print("Endpoints:")
        print("- GET /")
        print("- GET /users/<user_id>")
        print("- POST /login")
        
        return app
        
    except ImportError as e:
        print(f"Flask not available: {e}")
        print("Install with: pip install kakashi[flask]")
        return None


def django_example_setup():
    """Example of Django settings configuration for mylogs."""
    print("\n=== Django Integration Example ===")
    
    try:
        # This would go in your Django settings.py
        django_settings_example = '''
# settings.py

# Add mylogs middleware to MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Add mylogs middleware
    'mylogs.integrations.django_integration.DjangoLoggingMiddleware',
]

# Configure mylogs for Django
MYLOGS_CONFIG = {
    'logger_name': 'django_app',
    'log_file': 'django_app',
    'exclude_paths': ['/static/', '/media/', '/admin/jsi18n/', '/favicon.ico']
}

# Optional: Configure Django's built-in logging to work with mylogs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mylogs': {
            'class': 'mylogs.core.logger.MyLogsHandler',  # Custom handler if needed
        },
    },
    'root': {
        'handlers': ['mylogs'],
    },
}
'''
        
        # Example views.py
        views_example = '''
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
import json

        from kakashi.integrations.django_integration import DjangoLogger, log_django_error
        from kakashi.core import get_logger

# Initialize Django-specific logger
django_logger = DjangoLogger("views", "django_views")
business_logger = get_logger("business", "django_business")

def home(request):
    """Home view with logging."""
    business_logger.info("Home view accessed")
    
    # Log view access with user info
    user_id = str(request.user.id) if request.user.is_authenticated else None
    django_logger.log_view_access("home", user_id, request.user.is_authenticated)
    
    return JsonResponse({"message": "Hello World", "framework": "Django"})

def get_user(request, user_id):
    """Get user view with logging."""
    business_logger.info(f"Fetching user with ID: {user_id}")
    
    try:
        if int(user_id) <= 0:
            business_logger.warning(f"Invalid user ID requested: {user_id}")
            return JsonResponse({"error": "Invalid user ID"}, status=400)
        
        # Simulate database operation
        django_logger.log_database_query(f"SELECT * FROM auth_user WHERE id = {user_id}", 0.02)
        
        # Simulate model operation
        django_logger.log_model_operation("User", "read", user_id)
        
        user_data = {"id": int(user_id), "name": f"User {user_id}"}
        business_logger.info(f"User data retrieved: {user_data}")
        
        return JsonResponse(user_data)
        
    except Exception as e:
        log_django_error(e, "get_user", 
                        str(request.user.id) if request.user.is_authenticated else None)
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def login_view(request):
    """Login view with authentication logging."""
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username', '')
        password = data.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            django_logger.log_authentication_attempt(username, True)
            return JsonResponse({"token": "example-jwt-token", "user": username})
        else:
            django_logger.log_authentication_attempt(username, False)
            return JsonResponse({"error": "Authentication failed"}, status=401)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)
'''
        
        # Example management command
        command_example = '''
# management/commands/example_command.py
from django.core.management.base import BaseCommand
        from kakashi.integrations.django_integration import log_management_command

@log_management_command("example_task")
class Command(BaseCommand):
    help = 'Example management command with logging'
    
    def handle(self, *args, **options):
        self.stdout.write("Running example command...")
        # Your command logic here
        self.stdout.write(self.style.SUCCESS("Command completed successfully"))
'''
        
        print("Django integration configuration:")
        print("1. Add to settings.py:")
        print(django_settings_example)
        print("\n2. Example views.py:")
        print(views_example)
        print("\n3. Example management command:")
        print(command_example)
        
        return {
            'settings': django_settings_example,
            'views': views_example,
            'command': command_example
        }
        
    except Exception as e:
        print(f"Django example setup failed: {e}")
        return None


def run_all_examples():
    """Run all available web framework examples."""
    print("=== Kakashi Web Framework Integration Examples ===")
    print("This demonstrates kakashi integration with popular Python web frameworks.")
    print()
    
    # FastAPI example
    fastapi_app = fastapi_example()
    
    # Flask example  
    flask_app = flask_example()
    
    # Django configuration example
    django_config = django_example_setup()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("Check the logs/modules/ directory for framework-specific log files.")
    
    return {
        'fastapi': fastapi_app,
        'flask': flask_app, 
        'django': django_config
    }


if __name__ == "__main__":
    run_all_examples()
