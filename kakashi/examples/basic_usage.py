"""
Basic usage examples of mylogs without any framework dependencies.

This demonstrates the core logging functionality that works in any Python application.
"""

import time
import random
from typing import List, Tuple
from kakashi import get_logger, setup_logging, set_request_context, clear_request_context


def main() -> None:
    """Main function demonstrating basic mylogs usage."""
    
    print("=== Kakashi Basic Usage Examples ===")
    print("This example shows kakashi core functionality without any web framework.")
    print()
    
    # Setup logging for development environment
    setup_logging('development')
    
    # 1. Default logger - logs to app.log
    print("1. Basic logging:")
    default_logger = get_logger(__name__)
    default_logger.info("This is a basic info message")
    default_logger.warning("This is a warning message")
    default_logger.error("This is an error message")
    default_logger.debug("This is a debug message")
    
    # 2. Custom log files for different modules
    print("2. Module-specific log files:")
    
    # Database operations logger
    db_logger = get_logger(__name__, "database")
    db_logger.info("Database connection established")
    db_logger.debug("Executing SQL query: SELECT * FROM users")
    db_logger.warning("Database connection pool is 80% full")
    
    # API operations logger  
    api_logger = get_logger(__name__, "api")
    api_logger.info("API endpoint /users called")
    api_logger.debug("Request parameters: {'page': 1, 'limit': 10}")
    api_logger.error("User not found with ID: 12345")
    
    # Authentication logger
    auth_logger = get_logger(__name__, "authentication")
    auth_logger.info("User login attempt: john.doe@example.com")
    auth_logger.warning("Failed login attempt for user: admin@example.com")
    auth_logger.info("User logout: jane.smith@example.com")
    
    # 3. Context-based logging (simulating web requests)
    print("3. Context-based logging:")
    
    # Simulate different types of operations with context
    simulate_user_operations()
    simulate_batch_processing()
    simulate_background_tasks()
    
    # 4. Different formatter types
    print("4. Different formatter types:")
    
    # JSON formatter for structured logging
    json_logger = get_logger("json_example", "structured", "json")
    json_logger.info("This is a JSON formatted log entry")
    json_logger.error("JSON error message with structured data")
    
    # Compact formatter for resource-constrained environments
    compact_logger = get_logger("compact_example", "compact", "compact")  
    compact_logger.info("Compact log message")
    compact_logger.debug("Compact debug message")
    
    print()
    print("Check the logs/ directory for the following files:")
    print("- app.log (default logs)")
    print("- modules/database.log")
    print("- modules/api.log") 
    print("- modules/authentication.log")
    print("- modules/user_operations.log")
    print("- modules/batch_processing.log")
    print("- modules/background_tasks.log")
    print("- modules/structured.log (JSON format)")
    print("- modules/compact.log (compact format)")
    
    default_logger.info("Basic usage examples completed successfully")


def simulate_user_operations() -> None:
    """Simulate user operations with context tracking."""
    user_logger = get_logger(__name__, "user_operations")
    
    # Simulate different users and operations
    users: List[Tuple[str, str, str]] = [
        ("192.168.1.100", "john.doe@example.com", "GET /profile"),
        ("192.168.1.101", "jane.smith@example.com", "POST /update-profile"),
        ("192.168.1.102", "admin@example.com", "DELETE /user/123"),
    ]
    
    for ip, user, operation in users:
        # Set request context to simulate web request
        set_request_context(ip, operation)
        
        user_logger.info(f"User operation started for {user}")
        
        # Simulate some processing time
        time.sleep(0.1)
        
        if "DELETE" in operation:
            user_logger.warning(f"Destructive operation performed by {user}")
        
        user_logger.info(f"User operation completed for {user}")
        
        # Clear context
        clear_request_context()


def simulate_batch_processing() -> None:
    """Simulate batch processing operations."""
    batch_logger = get_logger(__name__, "batch_processing")
    
    batch_logger.info("Starting batch processing job")
    
    # Simulate processing multiple items
    items = ["item_1", "item_2", "item_3", "item_4", "item_5"]
    
    for i, item in enumerate(items, 1):
        # Set context with batch information
        set_request_context("BATCH_PROCESS", f"Processing {i}/{len(items)}")
        
        batch_logger.debug(f"Processing {item}")
        
        # Simulate processing time and occasional errors
        time.sleep(0.05)
        
        if random.random() > 0.8:  # 20% chance of warning
            batch_logger.warning(f"Slow processing detected for {item}")
        
        batch_logger.info(f"Successfully processed {item}")
        
        clear_request_context()
    
    batch_logger.info("Batch processing job completed")


def simulate_background_tasks() -> None:
    """Simulate background tasks."""
    task_logger = get_logger(__name__, "background_tasks")
    
    tasks = [
        "send_email_notifications",
        "cleanup_temp_files", 
        "generate_daily_report",
        "backup_database"
    ]
    
    for task in tasks:
        set_request_context("BACKGROUND", f"TASK: {task}")
        
        task_logger.info(f"Background task started: {task}")
        
        # Simulate task execution
        start_time = time.time()
        time.sleep(random.uniform(0.1, 0.3))  # Random processing time
        duration = time.time() - start_time
        
        if task == "backup_database":
            task_logger.warning(f"Long-running task: {task} took {duration:.2f}s")
        else:
            task_logger.info(f"Background task completed: {task} in {duration:.2f}s")
        
        clear_request_context()


def demonstrate_error_handling() -> None:
    """Demonstrate error handling with logging."""
    error_logger = get_logger(__name__, "error_handling")
    
    error_logger.info("Demonstrating error handling")
    
    try:
        # Simulate an error
        10 / 0
    except ZeroDivisionError as e:
        error_logger.error(f"Mathematical error occurred: {e}")
        error_logger.debug("This was intentional for demonstration purposes")
    
    try:
        # Simulate a file operation error
        with open("non_existent_file.txt", "r") as f:
            f.read()
    except FileNotFoundError as e:
        error_logger.error(f"File operation failed: {e}")
    
    error_logger.info("Error handling demonstration completed")


if __name__ == "__main__":
    main()
    demonstrate_error_handling()
