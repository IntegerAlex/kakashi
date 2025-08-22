"""
Example of using mylogs in a GUI application.

This demonstrates how mylogs can be used in desktop applications built with
tkinter, PyQt, or any other GUI framework.
"""

import time
import threading
from kakashi import get_logger, setup_logging, set_custom_context, clear_request_context


class GUIApplication:
    """Example GUI application with integrated logging."""
    
    def __init__(self):
        """Initialize the GUI application with logging."""
        # Setup logging for development
        setup_logging('development')
        
        # Get loggers for different components
        self.app_logger = get_logger("gui_app", "gui_application")
        self.ui_logger = get_logger("gui_ui", "gui_events")
        self.business_logger = get_logger("gui_business", "gui_business_logic")
        
        self.app_logger.info("GUI Application starting up")
        
        # Simulate application state
        self.user_id = "user123"
        self.session_id = "session456"
        self.is_running = True
    
    def handle_button_click(self, button_name: str):
        """Handle button click events with logging."""
        # Set context for this UI event
        set_custom_context(
            event_type="button_click",
            button=button_name,
            user_id=self.user_id,
            session_id=self.session_id
        )
        
        self.ui_logger.info(f"Button clicked: {button_name}")
        
        # Simulate different button actions
        if button_name == "save":
            self.handle_save_action()
        elif button_name == "load":
            self.handle_load_action()
        elif button_name == "delete":
            self.handle_delete_action()
        elif button_name == "refresh":
            self.handle_refresh_action()
        
        clear_request_context()
    
    def handle_save_action(self):
        """Handle save action with business logic logging."""
        self.business_logger.info("Save action initiated")
        
        try:
            # Simulate validation
            self.validate_data()
            
            # Simulate database save
            self.save_to_database()
            
            # Simulate file system operation
            self.save_to_file()
            
            self.business_logger.info("Save action completed successfully")
            self.show_message("Data saved successfully!")
            
        except Exception as e:
            self.business_logger.error(f"Save action failed: {e}")
            self.show_error(f"Failed to save: {e}")
    
    def handle_load_action(self):
        """Handle load action with performance logging."""
        start_time = time.time()
        self.business_logger.info("Load action initiated")
        
        try:
            # Simulate loading data
            data = self.load_from_database()
            self.populate_ui(data)
            
            duration = time.time() - start_time
            self.business_logger.info(f"Load action completed in {duration:.3f}s")
            self.show_message(f"Data loaded in {duration:.3f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            self.business_logger.error(f"Load action failed after {duration:.3f}s: {e}")
            self.show_error(f"Failed to load: {e}")
    
    def handle_delete_action(self):
        """Handle delete action with security logging."""
        self.business_logger.warning("Delete action initiated - destructive operation")
        
        try:
            # Simulate confirmation check
            if not self.confirm_delete():
                self.business_logger.info("Delete action cancelled by user")
                return
            
            # Simulate deletion
            self.delete_from_database()
            
            self.business_logger.warning("Delete action completed - data removed")
            self.show_message("Data deleted successfully!")
            
        except Exception as e:
            self.business_logger.error(f"Delete action failed: {e}")
            self.show_error(f"Failed to delete: {e}")
    
    def handle_refresh_action(self):
        """Handle refresh action with background processing."""
        self.ui_logger.info("Refresh action initiated")
        
        # Start background thread for refresh
        thread = threading.Thread(target=self.background_refresh)
        thread.daemon = True
        thread.start()
    
    def background_refresh(self):
        """Background refresh with separate thread logging."""
        # Set context for background operation
        set_custom_context(
            operation_type="background_refresh",
            thread_id=threading.current_thread().ident,
            user_id=self.user_id
        )
        
        bg_logger = get_logger("gui_background", "gui_background")
        bg_logger.info("Background refresh started")
        
        try:
            # Simulate multiple background tasks
            tasks = ["sync_data", "update_cache", "check_updates", "cleanup_temp"]
            
            for i, task in enumerate(tasks, 1):
                bg_logger.debug(f"Executing background task {i}/{len(tasks)}: {task}")
                time.sleep(0.5)  # Simulate work
                bg_logger.debug(f"Completed background task: {task}")
            
            bg_logger.info("Background refresh completed successfully")
            self.dispatch_ui_update("Refresh completed!")
            
        except Exception as e:
            bg_logger.error(f"Background refresh failed: {e}")
            self.dispatch_ui_update(f"Refresh failed: {e}")
        finally:
            clear_request_context()
    
    def validate_data(self):
        """Simulate data validation."""
        self.business_logger.debug("Validating data...")
        time.sleep(0.1)
        
        # Simulate occasional validation errors
        import random
        if random.random() > 0.9:
            raise ValueError("Invalid data format")
        
        self.business_logger.debug("Data validation passed")
    
    def save_to_database(self):
        """Simulate database save operation."""
        self.business_logger.debug("Saving to database...")
        time.sleep(0.2)
        self.business_logger.debug("Database save completed")
    
    def save_to_file(self):
        """Simulate file save operation."""
        self.business_logger.debug("Saving to file...")
        time.sleep(0.1)
        self.business_logger.debug("File save completed")
    
    def load_from_database(self):
        """Simulate database load operation."""
        self.business_logger.debug("Loading from database...")
        time.sleep(0.3)
        self.business_logger.debug("Database load completed")
        return {"records": 150, "last_updated": time.time()}
    
    def populate_ui(self, data):
        """Simulate UI population."""
        self.ui_logger.debug(f"Populating UI with {data.get('records', 0)} records")
        time.sleep(0.1)
        self.ui_logger.debug("UI population completed")
    
    def confirm_delete(self):
        """Simulate delete confirmation."""
        self.ui_logger.debug("Showing delete confirmation dialog")
        # Always confirm for demo
        return True
    
    def delete_from_database(self):
        """Simulate database deletion."""
        self.business_logger.debug("Deleting from database...")
        time.sleep(0.2)
        self.business_logger.debug("Database deletion completed")
    
    def show_message(self, message: str):
        """Simulate showing success message."""
        self.ui_logger.info(f"Showing message to user: {message}")
    
    def show_error(self, error: str):
        """Simulate showing error message."""
        self.ui_logger.error(f"Showing error to user: {error}")
    
    def dispatch_ui_update(self, message: str):
        """Simulate dispatching UI update from background thread."""
        self.ui_logger.info(f"Background operation completed: {message}")
    
    def handle_window_event(self, event_type: str):
        """Handle window events with logging."""
        set_custom_context(event_type="window_event", window_event=event_type)
        
        if event_type == "minimize":
            self.ui_logger.debug("Application minimized")
        elif event_type == "maximize": 
            self.ui_logger.debug("Application maximized")
        elif event_type == "close":
            self.ui_logger.info("Application close requested")
            self.shutdown()
        elif event_type == "focus":
            self.ui_logger.debug("Application gained focus")
        elif event_type == "blur":
            self.ui_logger.debug("Application lost focus")
        
        clear_request_context()
    
    def shutdown(self):
        """Shutdown the application with logging."""
        self.app_logger.info("Application shutdown initiated")
        
        # Simulate cleanup operations
        cleanup_tasks = ["save_preferences", "close_database", "cleanup_temp_files"]
        
        for task in cleanup_tasks:
            self.app_logger.debug(f"Cleanup task: {task}")
            time.sleep(0.1)
        
        self.is_running = False
        self.app_logger.info("Application shutdown completed")


def gui_example():
    """Run the GUI application example."""
    print("=== GUI Application Logging Example ===")
    print("This demonstrates mylogs usage in a desktop GUI application")
    print()
    
    # Create and run the GUI application
    app = GUIApplication()
    
    # Simulate user interactions
    print("Simulating user interactions...")
    
    # Simulate button clicks
    buttons = ["save", "load", "refresh", "delete"]
    for button in buttons:
        print(f"Simulating {button} button click...")
        app.handle_button_click(button)
        time.sleep(1)  # Pause between actions
    
    # Simulate window events
    window_events = ["minimize", "maximize", "focus", "blur"]
    for event in window_events:
        print(f"Simulating {event} window event...")
        app.handle_window_event(event)
        time.sleep(0.5)
    
    # Wait for background operations to complete
    print("Waiting for background operations to complete...")
    time.sleep(3)
    
    # Shutdown
    print("Shutting down application...")
    app.handle_window_event("close")
    
    print()
    print("GUI application example completed!")
    print("Check the logs/modules/ directory for GUI-specific log files:")
    print("- gui_application.log (main application events)")
    print("- gui_events.log (UI interaction events)")
    print("- gui_business_logic.log (business logic operations)")
    print("- gui_background.log (background operations)")


if __name__ == "__main__":
    gui_example()
