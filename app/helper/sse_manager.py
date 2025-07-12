"""
Advanced Server-Sent Events (SSE) management class for FastAPI
Handles client-specific and broadcast event distribution
"""

import logging
import queue
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SseManager:
    """
    Advanced Server-Sent Events (SSE) management class
    Handles client-specific and broadcast event distribution
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SseManager, cls).__new__(cls)
                    cls._instance.initialize()
        return cls._instance

    def initialize(self):
        """Initialize the SSE manager"""
        # Thread-safe dictionary for connected clients
        self.connected_clients: Dict[str, queue.Queue] = {}
        self.clients_lock = threading.Lock()
        # Shutdown flag
        self.is_shutting_down = False
        logger.info("SSE Manager initialized")

    def add_client(self, client_id: str, client_queue: queue.Queue):
        """
        Register a new client connection

        Args:
            client_id: Unique identifier for the client
            client_queue: Queue for sending events to the client
        """
        with self.clients_lock:
            self.connected_clients[client_id] = client_queue
        logger.info(f"New client connected: {client_id}")

    def remove_client(self, client_id: str):
        """
        Remove a client connection

        Args:
            client_id: Unique identifier for the client to remove
        """
        with self.clients_lock:
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
                logger.info(f"Client disconnected: {client_id}")

    def send_update(self, event_name: str, data: Any, client_id: Optional[str] = None):
        """
        Send an update to specific client or broadcast to all clients

        Args:
            event_name: Name of the event type
            data: Event data to send
            client_id: Optional specific client ID to send to. If None,
                      broadcasts to all clients
        """
        event = {
            "event": "message",
            "data": data,
            "type": event_name,
            "timestamp": time.time(),
            "client_id": client_id,  # Include client_id in the event
        }

        with self.clients_lock:
            # If client_id is specified, send to that specific client
            if client_id and client_id in self.connected_clients:
                try:
                    self.connected_clients[client_id].put(event, block=False)
                    logger.info(f"Event sent to specific client: {client_id}")
                except queue.Full:
                    logger.warning(f"Client {client_id} queue is full, skipping event")
            # If no client_id, broadcast to all clients
            else:
                for client_queue in self.connected_clients.values():
                    try:
                        client_queue.put(event, block=False)
                    except queue.Full:
                        logger.warning("A client queue is full, skipping event")
                client_count = len(self.connected_clients)
                logger.info(f"Event broadcasted to {client_count} clients")

    def get_connected_clients_count(self) -> int:
        """
        Get the number of currently connected clients

        Returns:
            Number of connected clients
        """
        with self.clients_lock:
            return len(self.connected_clients)

    def get_connected_client_ids(self) -> list:
        """
        Get list of currently connected client IDs

        Returns:
            List of client IDs
        """
        with self.clients_lock:
            return list(self.connected_clients.keys())

    def clear_clients(self):
        """
        Clear all connected clients
        """
        with self.clients_lock:
            self.connected_clients.clear()
        logger.info("All clients cleared")

    def shutdown(self):
        """
        Graceful shutdown of SSE manager
        """
        self.is_shutting_down = True
        self.clear_clients()
        logger.info("SSE Manager shutting down")

    def is_client_connected(self, client_id: str) -> bool:
        """
        Check if a specific client is connected

        Args:
            client_id: Client ID to check

        Returns:
            True if client is connected, False otherwise
        """
        with self.clients_lock:
            return client_id in self.connected_clients


# Create a singleton instance
sse_manager = SseManager()
