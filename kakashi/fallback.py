"""
Fallback logger implementations for kakashi.

This module contains emergency fallback loggers that are used when the main
logging system fails or is unavailable.
"""

import sys
from typing import Any


class FallbackLogger:
    """Minimal fallback logger that just prints to stderr."""
    
    def debug(self, message: str, **kwargs): 
        try: 
            print(f"[DEBUG] {message}", file=sys.stderr)
        except: 
            pass
    
    def info(self, message: str, **kwargs): 
        try: 
            print(f"[INFO] {message}", file=sys.stderr)
        except: 
            pass
    
    def warning(self, message: str, **kwargs): 
        try: 
            print(f"[WARNING] {message}", file=sys.stderr)
        except: 
            pass
    
    def error(self, message: str, **kwargs): 
        try: 
            print(f"[ERROR] {message}", file=sys.stderr)
        except: 
            pass
    
    def critical(self, message: str, **kwargs): 
        try: 
            print(f"[CRITICAL] {message}", file=sys.stderr)
        except: 
            pass
    
    def exception(self, message: str, **kwargs): 
        try: 
            print(f"[EXCEPTION] {message}", file=sys.stderr)
        except: 
            pass


class EmergencyLogger:
    """Emergency logger used when even basic setup fails."""
    
    def debug(self, message: str, **kwargs): 
        try: 
            print(f"[EMERGENCY-DEBUG] {message}", file=sys.stderr)
        except: 
            pass
    
    def info(self, message: str, **kwargs): 
        try: 
            print(f"[EMERGENCY-INFO] {message}", file=sys.stderr)
        except: 
            pass
    
    def warning(self, message: str, **kwargs): 
        try: 
            print(f"[EMERGENCY-WARNING] {message}", file=sys.stderr)
        except: 
            pass
    
    def error(self, message: str, **kwargs): 
        try: 
            print(f"[EMERGENCY-ERROR] {message}", file=sys.stderr)
        except: 
            pass
    
    def critical(self, message: str, **kwargs): 
        try: 
            print(f"[EMERGENCY-CRITICAL] {message}", file=sys.stderr)
        except: 
            pass
    
    def exception(self, message: str, **kwargs): 
        try: 
            print(f"[EMERGENCY-EXCEPTION] {message}", file=sys.stderr)
        except: 
            pass


class NoOpLogger:
    """Complete no-op logger used as last resort."""
    
    def debug(self, message: str, **kwargs: Any) -> None: 
        pass
    
    def info(self, message: str, **kwargs: Any) -> None: 
        pass
    
    def warning(self, message: str, **kwargs: Any) -> None: 
        pass
    
    def error(self, message: str, **kwargs: Any) -> None: 
        pass
    
    def critical(self, message: str, **kwargs: Any) -> None: 
        pass
    
    def exception(self, message: str, **kwargs: Any) -> None: 
        pass
