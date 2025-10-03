import threading
import time
from functools import wraps
from typing import Callable, Any, Dict
from PyQt6.QtCore import QTimer, QObject, pyqtSignal


class DebounceManager:
    """
    Manager class to handle debounced function calls
    """

    def __init__(self):
        self._timers: Dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def debounce(self, wait: float = 0.5, immediate: bool = False):
        """
        Decorator that debounces function calls

        Args:
            wait: Time to wait in seconds before executing the function
            immediate: If True, trigger the function on the leading edge instead of trailing edge

        Returns:
            Decorated function
        """

        def decorator(func: Callable) -> Callable:
            func_id = f"{func.__module__}.{func.__qualname__}"

            @wraps(func)
            def wrapper(*args, **kwargs):
                def call_it():
                    with self._lock:
                        if func_id in self._timers:
                            del self._timers[func_id]
                    return func(*args, **kwargs)

                with self._lock:
                    # Cancel existing timer if it exists
                    if func_id in self._timers:
                        self._timers[func_id].cancel()
                        del self._timers[func_id]

                    if immediate and func_id not in self._timers:
                        # Execute immediately on first call
                        result = func(*args, **kwargs)
                        # Still set up timer to prevent subsequent calls
                        timer = threading.Timer(wait, lambda: None)
                        timer.start()
                        self._timers[func_id] = timer
                        return result
                    else:
                        # Execute after delay (trailing edge)
                        timer = threading.Timer(wait, call_it)
                        timer.start()
                        self._timers[func_id] = timer
                        return None

            return wrapper

        return decorator

    def cancel_debounce(self, func: Callable):
        """Cancel pending debounced call for a specific function"""
        func_id = f"{func.__module__}.{func.__qualname__}"
        with self._lock:
            if func_id in self._timers:
                self._timers[func_id].cancel()
                del self._timers[func_id]

    def cancel_all(self):
        """Cancel all pending debounced calls"""
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()


class QtDebounceManager(QObject):
    """
    Qt-specific debounce manager using QTimer for better integration with Qt event loop
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timers: Dict[str, QTimer] = {}

    def debounce(self, wait: int = 500, immediate: bool = False):
        """
        Qt-specific debounce decorator using QTimer

        Args:
            wait: Time to wait in milliseconds before executing the function
            immediate: If True, trigger the function on the leading edge

        Returns:
            Decorated function
        """

        def decorator(func: Callable) -> Callable:
            func_id = f"{func.__module__}.{func.__qualname__}"

            @wraps(func)
            def wrapper(*args, **kwargs):
                # Stop existing timer
                if func_id in self._timers:
                    self._timers[func_id].stop()
                    self._timers[func_id].deleteLater()

                if immediate and func_id not in self._timers:
                    # Execute immediately on first call
                    result = func(*args, **kwargs)
                    # Set up timer to prevent subsequent calls
                    timer = QTimer()
                    timer.setSingleShot(True)
                    timer.timeout.connect(lambda: self._cleanup_timer(func_id))
                    timer.start(wait)
                    self._timers[func_id] = timer
                    return result
                else:
                    # Execute after delay
                    timer = QTimer()
                    timer.setSingleShot(True)
                    timer.timeout.connect(
                        lambda: self._execute_and_cleanup(func_id, func, args, kwargs)
                    )
                    timer.start(wait)
                    self._timers[func_id] = timer
                    return None

            return wrapper

        return decorator

    def _execute_and_cleanup(
        self, func_id: str, func: Callable, args: tuple, kwargs: dict
    ):
        """Execute function and cleanup timer"""
        try:
            func(*args, **kwargs)
        finally:
            self._cleanup_timer(func_id)

    def _cleanup_timer(self, func_id: str):
        """Cleanup timer after execution"""
        if func_id in self._timers:
            self._timers[func_id].deleteLater()
            del self._timers[func_id]

    def cancel_debounce(self, func: Callable):
        """Cancel pending debounced call for a specific function"""
        func_id = f"{func.__module__}.{func.__qualname__}"
        if func_id in self._timers:
            self._timers[func_id].stop()
            self._timers[func_id].deleteLater()
            del self._timers[func_id]

    def cancel_all(self):
        """Cancel all pending debounced calls"""
        for timer in self._timers.values():
            timer.stop()
            timer.deleteLater()
        self._timers.clear()


# Global instances for easy usage
debounce_manager = DebounceManager()
qt_debounce_manager = QtDebounceManager()


# Convenience decorators
def debounce(wait: float = 0.5, immediate: bool = False):
    """
    Standard debounce decorator using threading.Timer

    Usage:
        @debounce(wait=1.0)
        def search_function(query):
            print(f"Searching for: {query}")
    """
    return debounce_manager.debounce(wait, immediate)


def pyqtDebounce(wait: int = 500, immediate: bool = False):
    """
    Qt-specific debounce decorator using QTimer

    Usage:
        @qt_debounce(wait=1000)
        def on_text_changed(self, text):
            print(f"Text changed to: {text}")
    """
    return qt_debounce_manager.debounce(wait, immediate)


# Alternative implementation for method debouncing with instance-specific timers
def method_debounce(
    wait: float = 0.5, immediate: bool = False, attr_name: str = "_debounce_timers"
):
    """
    Debounce decorator for class methods that stores timers as instance attributes

    Args:
        wait: Time to wait in seconds
        immediate: Execute on leading edge
        attr_name: Attribute name to store timers dict on the instance

    Usage:
        class MyClass:
            @method_debounce(wait=1.0)
            def search(self, query):
                print(f"Searching: {query}")
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Initialize timers dict if it doesn't exist
            if not hasattr(self, attr_name):
                setattr(self, attr_name, {})

            timers = getattr(self, attr_name)
            func_name = func.__name__

            # Cancel existing timer
            if func_name in timers:
                timers[func_name].cancel()

            def call_it():
                if func_name in timers:
                    del timers[func_name]
                return func(self, *args, **kwargs)

            if immediate and func_name not in timers:
                # Execute immediately
                result = func(self, *args, **kwargs)
                # Set timer to prevent subsequent calls
                timer = threading.Timer(wait, lambda: timers.pop(func_name, None))
                timer.start()
                timers[func_name] = timer
                return result
            else:
                # Execute after delay
                timer = threading.Timer(wait, call_it)
                timer.start()
                timers[func_name] = timer
                return None

        return wrapper

    return decorator
