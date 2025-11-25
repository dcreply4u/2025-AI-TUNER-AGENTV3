"""
UI Optimizer

Optimizes UI responsiveness, memory usage, and screen switching performance.
"""

from __future__ import annotations

import gc
import logging
import weakref
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QWidget

LOGGER = logging.getLogger(__name__)


class LazyWidget:
    """Lazy-loading widget wrapper."""

    def __init__(self, widget_class: type, *args, **kwargs):
        self.widget_class = widget_class
        self.args = args
        self.kwargs = kwargs
        self._widget: Optional[QWidget] = None
        self._loaded = False

    def get(self) -> QWidget:
        """Get widget, creating it if needed."""
        if not self._loaded:
            self._widget = self.widget_class(*self.args, **self.kwargs)
            self._loaded = True
        return self._widget

    def unload(self) -> None:
        """Unload widget to free memory."""
        if self._widget:
            self._widget.deleteLater()
            self._widget = None
            self._loaded = False
            gc.collect()


class UIOptimizer:
    """Optimizes UI performance and memory usage."""

    def __init__(self) -> None:
        """Initialize UI optimizer."""
        self.lazy_widgets: Dict[str, LazyWidget] = {}
        self.widget_cache: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._periodic_cleanup)
        self.cleanup_timer.start(30000)  # Cleanup every 30 seconds

    def register_lazy_widget(self, name: str, widget_class: type, *args, **kwargs) -> None:
        """Register a widget for lazy loading."""
        self.lazy_widgets[name] = LazyWidget(widget_class, *args, **kwargs)

    def get_lazy_widget(self, name: str) -> Optional[QWidget]:
        """Get a lazy-loaded widget."""
        if name in self.lazy_widgets:
            return self.lazy_widgets[name].get()
        return None

    def unload_unused_widgets(self) -> None:
        """Unload widgets that aren't currently visible."""
        for name, lazy_widget in self.lazy_widgets.items():
            if lazy_widget._loaded and lazy_widget._widget:
                if not lazy_widget._widget.isVisible():
                    lazy_widget.unload()

    def _periodic_cleanup(self) -> None:
        """Periodic cleanup of unused resources."""
        self.unload_unused_widgets()
        gc.collect()

    def optimize_widget(self, widget: QWidget) -> None:
        """Apply optimizations to a widget."""
        # Disable updates during heavy operations
        widget.setUpdatesEnabled(False)

        # Set attribute for efficient painting
        widget.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        widget.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # Enable native painting if possible
        widget.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, False)


def debounce(delay: float = 0.3):
    """Debounce decorator for expensive operations."""

    def decorator(func: Callable) -> Callable:
        timer: Optional[QTimer] = None

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal timer
            if timer:
                timer.stop()

            def call_func():
                func(*args, **kwargs)

            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(call_func)
            timer.start(int(delay * 1000))

        return wrapper

    return decorator


def throttle(limit: float = 0.1):
    """Throttle decorator to limit function call frequency."""

    def decorator(func: Callable) -> Callable:
        last_called = [0.0]

        @wraps(func)
        def wrapper(*args, **kwargs):
            import time

            now = time.time()
            if now - last_called[0] >= limit:
                last_called[0] = now
                return func(*args, **kwargs)

        return wrapper

    return decorator


class EfficientDataModel:
    """Efficient data model with pagination and caching."""

    def __init__(self, page_size: int = 100):
        self.page_size = page_size
        self._cache: Dict[int, list] = {}
        self._total_items = 0

    def get_page(self, page: int) -> list:
        """Get a page of data."""
        if page in self._cache:
            return self._cache[page]

        # Load page (would be implemented by subclass)
        data = self._load_page(page)
        self._cache[page] = data

        # Limit cache size
        if len(self._cache) > 10:
            oldest_page = min(self._cache.keys())
            del self._cache[oldest_page]

        return data

    def _load_page(self, page: int) -> list:
        """Load a page of data (to be implemented by subclass)."""
        return []

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear()


__all__ = ["UIOptimizer", "LazyWidget", "debounce", "throttle", "EfficientDataModel"]
