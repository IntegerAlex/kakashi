"""
Example of using mylogs in a CLI (Command Line Interface) application.

This demonstrates how mylogs can be used in command-line tools, scripts,
and batch processing applications.
"""

import argparse
import time
import os
from typing import List, Optional

from kakashi import (
    get_logger, setup_logging, set_custom_context, 
    clear_request_context, configure_colors
)


class CLIApplication:
    """Example CLI application with integrated logging."""
    
    def __init__(self, verbose: bool = False, log_file: Optional[str] = None):
        """Initialize CLI application with logging."""
        # Setup logging based on verbosity
        if verbose:
            setup_logging('development')
            configure_colors(console_colors=True, bright_colors=True)
        else:
            setup_logging('production')
            configure_colors(console_colors=False)
        
        # Get loggers for different components
        self.app_logger = get_logger("cli_app", log_file or "cli_application")
        self.operation_logger = get_logger("cli_operations", "cli_operations")
        self.file_logger = get_logger("cli_files", "cli_file_operations")
        
        self.verbose = verbose
        self.app_logger.info("CLI Application starting")
        
        if verbose:
            print("CLI Application started with verbose logging")
    
    def process_files(self, file_paths: List[str], operation: str = "analyze"):
        """Process multiple files with logging."""
        set_custom_context(
            operation_type="batch_file_processing",
            operation=operation,
            total_files=len(file_paths)
        )
        
        self.operation_logger.info(f"Starting {operation} operation on {len(file_paths)} files")
        
        if self.verbose:
            print(f"Processing {len(file_paths)} files with operation: {operation}")
        
        successful = 0
        failed = 0
        
        for i, file_path in enumerate(file_paths, 1):
            # Set context for each file
            set_custom_context(
                operation_type="file_processing",
                file_path=file_path,
                file_index=i,
                total_files=len(file_paths)
            )
            
            self.file_logger.info(f"Processing file {i}/{len(file_paths)}: {file_path}")
            
            try:
                if operation == "analyze":
                    result = self.analyze_file(file_path)
                elif operation == "convert":
                    result = self.convert_file(file_path)
                elif operation == "validate":
                    result = self.validate_file(file_path)
                else:
                    raise ValueError(f"Unknown operation: {operation}")
                
                successful += 1
                self.file_logger.info(f"Successfully processed: {file_path}")
                
                if self.verbose:
                    print(f"✓ {file_path}: {result}")
                    
            except Exception as e:
                failed += 1
                self.file_logger.error(f"Failed to process {file_path}: {e}")
                
                if self.verbose:
                    print(f"✗ {file_path}: {e}")
                else:
                    print(f"Error processing {file_path}: {e}")
        
        # Summary logging
        self.operation_logger.info(
            f"Batch processing completed: {successful} successful, {failed} failed"
        )
        
        print(f"\nProcessing completed: {successful} successful, {failed} failed")
        clear_request_context()
        
        return {"successful": successful, "failed": failed}
    
    def analyze_file(self, file_path: str) -> str:
        """Analyze a single file."""
        self.file_logger.debug(f"Starting analysis of: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Simulate file analysis
        file_size = os.path.getsize(file_path)
        time.sleep(0.1)  # Simulate processing time
        
        self.file_logger.debug(f"File analysis completed: {file_path} ({file_size} bytes)")
        
        return f"Size: {file_size} bytes"
    
    def convert_file(self, file_path: str) -> str:
        """Convert a single file."""
        self.file_logger.debug(f"Starting conversion of: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Simulate file conversion
        time.sleep(0.2)  # Simulate longer processing time
        
        # Simulate occasional conversion errors
        import random
        if random.random() > 0.8:
            raise RuntimeError("Conversion failed due to file format issues")
        
        output_path = file_path + ".converted"
        self.file_logger.debug(f"File conversion completed: {file_path} -> {output_path}")
        
        return f"Converted to: {output_path}"
    
    def validate_file(self, file_path: str) -> str:
        """Validate a single file."""
        self.file_logger.debug(f"Starting validation of: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Simulate file validation
        time.sleep(0.05)
        
        # Simulate validation results
        import random
        is_valid = random.random() > 0.1
        
        if is_valid:
            self.file_logger.debug(f"File validation passed: {file_path}")
            return "Valid"
        else:
            self.file_logger.warning(f"File validation failed: {file_path}")
            raise ValueError("File validation failed")
    
    def database_operation(self, operation: str, table: str, records: int = 100):
        """Simulate database operations."""
        set_custom_context(
            operation_type="database_operation",
            db_operation=operation,
            table=table,
            record_count=records
        )
        
        db_logger = get_logger("cli_database", "cli_database")
        db_logger.info(f"Starting database {operation} on {table} ({records} records)")
        
        if self.verbose:
            print(f"Database {operation}: {table} table, {records} records")
        
        start_time = time.time()
        
        try:
            if operation == "backup":
                self.simulate_backup(table, records)
            elif operation == "migrate":
                self.simulate_migration(table, records)
            elif operation == "cleanup":
                self.simulate_cleanup(table, records)
            else:
                raise ValueError(f"Unknown database operation: {operation}")
            
            duration = time.time() - start_time
            db_logger.info(f"Database {operation} completed in {duration:.3f}s")
            
            if self.verbose:
                print(f"✓ Database {operation} completed in {duration:.3f}s")
                
        except Exception as e:
            duration = time.time() - start_time
            db_logger.error(f"Database {operation} failed after {duration:.3f}s: {e}")
            
            print(f"✗ Database {operation} failed: {e}")
            raise
        finally:
            clear_request_context()
    
    def simulate_backup(self, table: str, records: int):
        """Simulate database backup."""
        db_logger = get_logger("cli_database", "cli_database")
        
        # Simulate backup process
        for i in range(0, records, 20):
            batch_size = min(20, records - i)
            db_logger.debug(f"Backing up records {i+1}-{i+batch_size} of {table}")
            time.sleep(0.01)
        
        db_logger.debug(f"Backup completed for {table}: {records} records")
    
    def simulate_migration(self, table: str, records: int):
        """Simulate database migration."""
        db_logger = get_logger("cli_database", "cli_database")
        
        # Simulate migration steps
        steps = ["validate_schema", "create_temp_table", "copy_data", "update_indexes", "cleanup"]
        
        for step in steps:
            db_logger.debug(f"Migration step: {step} for {table}")
            time.sleep(0.05)
        
        db_logger.debug(f"Migration completed for {table}: {records} records migrated")
    
    def simulate_cleanup(self, table: str, records: int):
        """Simulate database cleanup."""
        db_logger = get_logger("cli_database", "cli_database")
        
        # Simulate cleanup process
        deleted = int(records * 0.1)  # Delete 10% of records
        db_logger.debug(f"Cleanup process: removing {deleted} old records from {table}")
        time.sleep(0.1)
        
        db_logger.debug(f"Cleanup completed for {table}: {deleted} records removed")
    
    def run_scheduled_task(self, task_name: str):
        """Run a scheduled task with logging."""
        set_custom_context(
            operation_type="scheduled_task",
            task_name=task_name,
            scheduled_time=time.time()
        )
        
        task_logger = get_logger("cli_scheduler", "cli_scheduled_tasks")
        task_logger.info(f"Scheduled task started: {task_name}")
        
        if self.verbose:
            print(f"Running scheduled task: {task_name}")
        
        start_time = time.time()
        
        try:
            # Simulate different task types
            if task_name == "daily_report":
                self.generate_report()
            elif task_name == "data_sync":
                self.sync_data()
            elif task_name == "cache_refresh":
                self.refresh_cache()
            elif task_name == "log_rotation":
                self.rotate_logs()
            else:
                raise ValueError(f"Unknown scheduled task: {task_name}")
            
            duration = time.time() - start_time
            task_logger.info(f"Scheduled task completed: {task_name} in {duration:.3f}s")
            
            if self.verbose:
                print(f"✓ Task {task_name} completed in {duration:.3f}s")
                
        except Exception as e:
            duration = time.time() - start_time
            task_logger.error(f"Scheduled task failed: {task_name} after {duration:.3f}s: {e}")
            
            print(f"✗ Task {task_name} failed: {e}")
            raise
        finally:
            clear_request_context()
    
    def generate_report(self):
        """Simulate report generation."""
        time.sleep(0.3)
        self.operation_logger.debug("Daily report generated successfully")
    
    def sync_data(self):
        """Simulate data synchronization."""
        time.sleep(0.2)
        self.operation_logger.debug("Data synchronization completed")
    
    def refresh_cache(self):
        """Simulate cache refresh."""
        time.sleep(0.1)
        self.operation_logger.debug("Cache refresh completed")
    
    def rotate_logs(self):
        """Simulate log rotation."""
        time.sleep(0.05)
        self.operation_logger.debug("Log rotation completed")
    
    def shutdown(self):
        """Shutdown the CLI application."""
        self.app_logger.info("CLI Application shutting down")
        
        if self.verbose:
            print("CLI Application shutdown completed")


def cli_example(args: Optional[List[str]] = None):
    """Run the CLI application example."""
    print("=== CLI Application Logging Example ===")
    print("This demonstrates mylogs usage in command-line applications")
    print()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MyLogs CLI Example")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Enable verbose logging")
    parser.add_argument("--log-file", default="cli_example",
                       help="Custom log file name")
    parser.add_argument("--operation", choices=["files", "database", "tasks", "all"],
                       default="all", help="Operation to demonstrate")
    
    if args is None:
        # Use sys.argv when called from command line
        parsed_args = parser.parse_args()
    else:
        # Use provided args for testing
        parsed_args = parser.parse_args(args)
    
    # Create CLI application
    app = CLIApplication(verbose=parsed_args.verbose, log_file=parsed_args.log_file)
    
    try:
        if parsed_args.operation in ["files", "all"]:
            print("1. File Processing Operations:")
            # Create some dummy files for demonstration
            dummy_files = ["file1.txt", "file2.txt", "file3.txt", "missing_file.txt"]
            
            for operation in ["analyze", "validate", "convert"]:
                print(f"\n  Running {operation} operation:")
                app.process_files(dummy_files, operation)
        
        if parsed_args.operation in ["database", "all"]:
            print("\n2. Database Operations:")
            for db_op in ["backup", "migrate", "cleanup"]:
                print(f"\n  Running database {db_op}:")
                app.database_operation(db_op, "users", 500)
        
        if parsed_args.operation in ["tasks", "all"]:
            print("\n3. Scheduled Tasks:")
            tasks = ["daily_report", "data_sync", "cache_refresh", "log_rotation"]
            
            for task in tasks:
                print(f"\n  Running scheduled task: {task}")
                app.run_scheduled_task(task)
        
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
        app.app_logger.warning("Operation interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        app.app_logger.error(f"Unexpected error: {e}")
    finally:
        app.shutdown()
    
    print("\n" + "="*60)
    print("CLI application example completed!")
    print("Check the logs/modules/ directory for CLI-specific log files:")
    print("- cli_application.log (main application events)")
    print("- cli_operations.log (operation-specific events)")
    print("- cli_file_operations.log (file processing events)")
    print("- cli_database.log (database operation events)")
    print("- cli_scheduled_tasks.log (scheduled task events)")


if __name__ == "__main__":
    cli_example()
