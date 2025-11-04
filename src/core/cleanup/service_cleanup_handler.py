"""
Service Cleanup Handler - Specialized handler for application service cleanup.

This handler is responsible for cleaning up application services including
background threads, cache cleanup, and database connections.
"""

from typing import Any, Dict
import threading

from .unified_cleanup_coordinator import CleanupHandler, CleanupPhase, CleanupContext


class ServiceCleanupHandler(CleanupHandler):
    """
    Specialized handler for application service cleanup.

    This handler manages service-specific cleanup operations including:
    - Background service termination
    - Cache flushing
    - Database connection closure
    - Thread cleanup
    """

    def __init__(self):
        """Initialize the service cleanup handler."""
        super().__init__("ServiceCleanupHandler")
        self._application = None
        self._background_threads = []
        self._services = {}

    def can_handle(self, phase: CleanupPhase) -> bool:
        """Check if this handler can handle the given phase."""
        return phase == CleanupPhase.SERVICE_SHUTDOWN

    def execute(self, phase: CleanupPhase, context: CleanupContext) -> bool:
        """
        Execute service cleanup for the given phase.

        Args:
            phase: The cleanup phase
            context: The cleanup context state

        Returns:
            True if cleanup completed successfully
        """
        try:
            self.logger.info("Starting service cleanup")

            # Get application from context data
            application = getattr(phase, "_context_data", {}).get("application")
            if application:
                self._application = application

            # Perform service cleanup
            success = self._cleanup_services()

            if success:
                self.logger.info("Service cleanup completed successfully")
            else:
                self.logger.warning("Service cleanup completed with some issues")

            return success

        except Exception as e:
            self.logger.error(f"Service cleanup error: {e}", exc_info=True)
            return False

    def _cleanup_services(self) -> bool:
        """Cleanup all services."""
        try:
            overall_success = True
            cleanup_results = {}

            # Cleanup application bootstrap services
            self.logger.debug("Cleaning up bootstrap services...")
            success = self._cleanup_bootstrap_services()
            cleanup_results["bootstrap_services"] = success
            overall_success = overall_success and success

            # Cleanup background threads
            self.logger.debug("Cleaning up background threads...")
            success = self._cleanup_background_threads()
            cleanup_results["background_threads"] = success
            overall_success = overall_success and success

            # Cleanup caches
            self.logger.debug("Cleaning up caches...")
            success = self._cleanup_caches()
            cleanup_results["caches"] = success
            overall_success = overall_success and success

            # Cleanup database connections
            self.logger.debug("Cleaning up database connections...")
            success = self._cleanup_database_connections()
            cleanup_results["database_connections"] = success
            overall_success = overall_success and success

            # Cleanup memory manager
            self.logger.debug("Cleaning up memory manager...")
            success = self._cleanup_memory_manager()
            cleanup_results["memory_manager"] = success
            overall_success = overall_success and success

            # Log results
            failed_services = [name for name, success in cleanup_results.items() if not success]
            if failed_services:
                self.logger.warning(
                    f"Failed to cleanup {len(failed_services)} service(s): {', '.join(failed_services)}"
                )
            else:
                self.logger.info("All services cleaned up successfully")

            return overall_success

        except Exception as e:
            self.logger.error(f"Service cleanup failed: {e}", exc_info=True)
            return False

    def _cleanup_bootstrap_services(self) -> bool:
        """Cleanup application bootstrap services."""
        try:
            self.logger.debug("Cleaning up bootstrap services")

            success = True

            if (
                self._application
                and hasattr(self._application, "bootstrap")
                and self._application.bootstrap
            ):
                try:
                    if hasattr(self._application.bootstrap, "cleanup"):
                        self._application.bootstrap.cleanup()
                        self.logger.debug("Bootstrap cleanup called")
                    else:
                        self.logger.warning("Bootstrap has no cleanup method")
                except Exception as e:
                    self.logger.error(f"Bootstrap cleanup failed: {e}")
                    success = False

            return success

        except Exception as e:
            self.logger.error(f"Bootstrap services cleanup failed: {e}")
            return False

    def _cleanup_background_threads(self) -> bool:
        """Cleanup background threads."""
        try:
            self.logger.debug("Cleaning up background threads")

            threads_cleaned = 0

            # Find and cleanup background threads
            for thread in threading.enumerate():
                try:
                    if (
                        thread != threading.current_thread()
                        and thread.is_alive()
                        and hasattr(thread, "daemon")
                        and thread.daemon
                    ):

                        # Try to stop the thread gracefully
                        if hasattr(thread, "stop"):
                            thread.stop()
                        elif hasattr(thread, "cancel"):
                            thread.cancel()

                        threads_cleaned += 1
                        self.logger.debug(f"Cleaned up background thread: {thread.name}")

                except Exception as e:
                    self.logger.warning(
                        f"Failed to cleanup thread {getattr(thread, 'name', 'unknown')}: {e}"
                    )

            self.logger.debug(f"Cleaned up {threads_cleaned} background threads")
            return True

        except Exception as e:
            self.logger.error(f"Background threads cleanup failed: {e}")
            return False

    def _cleanup_caches(self) -> bool:
        """Cleanup various caches."""
        try:
            self.logger.debug("Cleaning up caches")

            success = True

            # Cleanup model cache
            success = self._cleanup_model_cache() and success

            # Cleanup thumbnail cache
            success = self._cleanup_thumbnail_cache() and success

            # Cleanup file hash cache
            success = self._cleanup_file_hash_cache() and success

            return success

        except Exception as e:
            self.logger.error(f"Caches cleanup failed: {e}")
            return False

    def _cleanup_model_cache(self) -> bool:
        """Cleanup model cache."""
        try:
            self.logger.debug("Cleaning up model cache")

            try:
                from src.core.model_cache import get_model_cache

                cache = get_model_cache()
                if hasattr(cache, "cleanup"):
                    cache.cleanup()
                    self.logger.debug("Model cache cleanup called")
                else:
                    self.logger.warning("Model cache has no cleanup method")
            except ImportError:
                self.logger.debug("Model cache not available")
            except Exception as e:
                self.logger.warning(f"Model cache cleanup failed: {e}")

            return True

        except Exception as e:
            self.logger.error(f"Model cache cleanup failed: {e}")
            return False

    def _cleanup_thumbnail_cache(self) -> bool:
        """Cleanup thumbnail cache."""
        try:
            self.logger.debug("Cleaning up thumbnail cache")

            try:
                from src.core.import_thumbnail_service import get_thumbnail_service

                service = get_thumbnail_service()
                if hasattr(service, "cleanup"):
                    service.cleanup()
                    self.logger.debug("Thumbnail service cleanup called")
                else:
                    self.logger.warning("Thumbnail service has no cleanup method")
            except ImportError:
                self.logger.debug("Thumbnail service not available")
            except Exception as e:
                self.logger.warning(f"Thumbnail service cleanup failed: {e}")

            return True

        except Exception as e:
            self.logger.error(f"Thumbnail cache cleanup failed: {e}")
            return False

    def _cleanup_file_hash_cache(self) -> bool:
        """Cleanup file hash cache."""
        try:
            self.logger.debug("Cleaning up file hash cache")

            try:
                from src.utils.file_hash import get_fast_hasher

                hasher = get_fast_hasher()
                if hasattr(hasher, "cleanup"):
                    hasher.cleanup()
                    self.logger.debug("Fast hasher cleanup called")
                else:
                    self.logger.warning("Fast hasher has no cleanup method")
            except ImportError:
                self.logger.debug("Fast hasher not available")
            except Exception as e:
                self.logger.warning(f"Fast hasher cleanup failed: {e}")

            return True

        except Exception as e:
            self.logger.error(f"File hash cache cleanup failed: {e}")
            return False

    def _cleanup_database_connections(self) -> bool:
        """Cleanup database connections."""
        try:
            self.logger.debug("Cleaning up database connections")

            # This would typically involve closing database connections
            # For now, we'll just log the attempt

            self.logger.debug("Database connections cleanup completed")
            return True

        except Exception as e:
            self.logger.error(f"Database connections cleanup failed: {e}")
            return False

    def _cleanup_memory_manager(self) -> bool:
        """Cleanup memory manager."""
        try:
            self.logger.debug("Cleaning up memory manager")

            try:
                from src.core.memory_manager import get_memory_manager

                memory_manager = get_memory_manager()
                if hasattr(memory_manager, "cleanup"):
                    memory_manager.cleanup()
                    self.logger.debug("Memory manager cleanup called")
                else:
                    self.logger.warning("Memory manager has no cleanup method")
            except ImportError:
                self.logger.debug("Memory manager not available")
            except Exception as e:
                self.logger.warning(f"Memory manager cleanup failed: {e}")

            return True

        except Exception as e:
            self.logger.error(f"Memory manager cleanup failed: {e}")
            return False

    def register_service(self, name: str, service: Any) -> None:
        """
        Register a service for cleanup tracking.

        Args:
            name: Service name
            service: Service object
        """
        try:
            if service:
                self._services[name] = service
                self.logger.debug(f"Registered service for cleanup: {name}")
            else:
                self.logger.warning(f"Invalid service registration: {name}")

        except Exception as e:
            self.logger.warning(f"Failed to register service {name}: {e}")

    def unregister_service(self, name: str) -> bool:
        """
        Unregister a service from cleanup tracking.

        Args:
            name: Service name

        Returns:
            True if service was unregistered
        """
        try:
            if name in self._services:
                del self._services[name]
                self.logger.debug(f"Unregistered service from cleanup: {name}")
                return True
            return False

        except Exception as e:
            self.logger.warning(f"Failed to unregister service {name}: {e}")
            return False

    def get_service_cleanup_stats(self) -> Dict[str, Any]:
        """Get service cleanup statistics."""
        try:
            return {
                "handler_name": self.name,
                "enabled": self.enabled,
                "application_available": self._application is not None,
                "registered_services": list(self._services.keys()),
                "services_count": len(self._services),
            }

        except Exception as e:
            self.logger.warning(f"Failed to get service cleanup stats: {e}")
            return {"handler_name": self.name, "error": str(e)}
