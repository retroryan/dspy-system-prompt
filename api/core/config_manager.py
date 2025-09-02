"""
Configuration management system.

Handles system configuration persistence, validation, and updates.
"""

import json
import os
import time
import logging
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from api.core.config_models import (
    LLMConfig, AgentConfig, ToolsConfig, APIConfig, 
    SystemHealthStatus, SystemMetrics, SystemAction
)

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages system configuration and metrics."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._load_all_configs()
        self._server_start_time = time.time()
    
    def get_config(self, section: str) -> Dict[str, Any]:
        """Get configuration for a section."""
        if section not in self._config_cache:
            self._load_config(section)
        
        return self._config_cache.get(section, {})
    
    def update_config(self, section: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration for a section."""
        # Validate configuration based on section
        validated_config = self._validate_config(section, config)
        
        # Update cache
        self._config_cache[section] = validated_config
        
        # Persist to file
        self._save_config(section, validated_config)
        
        logger.info(f"Updated configuration section: {section}")
        return validated_config
    
    def get_system_health(self) -> SystemHealthStatus:
        """Get current system health status."""
        try:
            # Get system metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Determine overall status
            status = "healthy"
            if cpu_percent > 80 or memory.percent > 85:
                status = "warning"
            if cpu_percent > 95 or memory.percent > 95:
                status = "error"
            
            # Calculate uptime
            uptime_seconds = time.time() - self._server_start_time
            uptime_str = self._format_uptime(uptime_seconds)
            
            return SystemHealthStatus(
                status=status,
                uptime=uptime_str,
                memory={
                    "used": memory.used / (1024 * 1024),  # MB
                    "total": memory.total / (1024 * 1024),  # MB
                    "percent": memory.percent
                },
                cpu=cpu_percent,
                active_connections=self._get_active_connections(),
                last_check=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Failed to get system health: {str(e)}")
            return SystemHealthStatus(
                status="error",
                uptime="unknown",
                memory={"used": 0, "total": 0, "percent": 0},
                cpu=0,
                active_connections=0,
                last_check=datetime.now().isoformat()
            )
    
    def get_system_metrics(self, demo_executor=None) -> SystemMetrics:
        """Get enhanced system metrics."""
        try:
            # Import metrics from health router
            from api.routers.health import metrics
            
            # Get system info
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            disk = psutil.disk_usage('/')
            
            # Get demo statistics if demo_executor provided
            active_demos = 0
            completed_demos = 0
            failed_demos = 0
            tool_executions = {}
            
            if demo_executor:
                demos = demo_executor.list_demos()
                active_demos = len([d for d in demos if d.status.value == "running"])
                completed_demos = len([d for d in demos if d.status.value == "completed"])
                failed_demos = len([d for d in demos if d.status.value == "failed"])
                
                # Count tool executions
                for demo in demos:
                    for tool in demo.tools_used:
                        tool_executions[tool] = tool_executions.get(tool, 0) + 1
            
            return SystemMetrics(
                total_requests=metrics.total_requests,
                total_queries=metrics.total_queries,
                active_sessions=self._get_active_sessions(),
                average_query_time=metrics.average_query_time,
                uptime_seconds=time.time() - self._server_start_time,
                memory_usage_mb=memory.used / (1024 * 1024),
                cpu_usage_percent=cpu_percent,
                disk_usage_percent=disk.percent,
                active_demos=active_demos,
                completed_demos=completed_demos,
                failed_demos=failed_demos,
                tool_executions=tool_executions
            )
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            # Return minimal metrics on error
            return SystemMetrics(
                uptime_seconds=time.time() - self._server_start_time
            )
    
    def perform_system_action(self, action: SystemAction, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform a system action."""
        try:
            if action == SystemAction.RESTART_SERVICES:
                return self._restart_services(parameters)
            elif action == SystemAction.CLEAR_CACHE:
                return self._clear_cache(parameters)
            elif action == SystemAction.EXPORT_DIAGNOSTICS:
                return self._export_diagnostics(parameters)
            elif action == SystemAction.VIEW_LOGS:
                return self._view_logs(parameters)
            else:
                raise ValueError(f"Unknown system action: {action}")
                
        except Exception as e:
            logger.error(f"System action {action} failed: {str(e)}")
            return {
                "success": False,
                "message": f"Action failed: {str(e)}"
            }
    
    def _load_all_configs(self):
        """Load all configuration sections."""
        sections = ["llm", "agent", "tools", "api"]
        for section in sections:
            self._load_config(section)
    
    def _load_config(self, section: str):
        """Load configuration from file."""
        config_file = self.config_dir / f"{section}.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                self._config_cache[section] = config
                logger.debug(f"Loaded config for section: {section}")
            except Exception as e:
                logger.error(f"Failed to load config for {section}: {str(e)}")
                self._config_cache[section] = self._get_default_config(section)
        else:
            # Use default configuration
            self._config_cache[section] = self._get_default_config(section)
    
    def _save_config(self, section: str, config: Dict[str, Any]):
        """Save configuration to file."""
        config_file = self.config_dir / f"{section}.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.debug(f"Saved config for section: {section}")
        except Exception as e:
            logger.error(f"Failed to save config for {section}: {str(e)}")
    
    def _get_default_config(self, section: str) -> Dict[str, Any]:
        """Get default configuration for a section."""
        defaults = {
            "llm": LLMConfig().model_dump(),
            "agent": AgentConfig().model_dump(),
            "tools": ToolsConfig().model_dump(),
            "api": APIConfig().model_dump()
        }
        
        return defaults.get(section, {})
    
    def _validate_config(self, section: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration based on section."""
        try:
            if section == "llm":
                validated = LLMConfig(**config)
            elif section == "agent":
                validated = AgentConfig(**config)
            elif section == "tools":
                validated = ToolsConfig(**config)
            elif section == "api":
                validated = APIConfig(**config)
            else:
                raise ValueError(f"Unknown config section: {section}")
            
            return validated.model_dump()
            
        except Exception as e:
            logger.error(f"Config validation failed for {section}: {str(e)}")
            raise ValueError(f"Invalid configuration: {str(e)}")
    
    def _get_active_sessions(self) -> int:
        """Get number of active sessions."""
        try:
            from api.core.sessions import session_manager
            return session_manager.get_active_session_count()
        except:
            return 0
    
    def _get_active_connections(self) -> int:
        """Get number of active network connections."""
        try:
            connections = psutil.net_connections(kind='inet')
            return len([c for c in connections if c.status == psutil.CONN_ESTABLISHED])
        except:
            return 0
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime seconds into human readable string."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _restart_services(self, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Restart services (simulated for safety)."""
        logger.warning("Service restart requested (simulated)")
        return {
            "success": True,
            "message": "Service restart simulated (use system tools for actual restart)"
        }
    
    def _clear_cache(self, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Clear system caches."""
        try:
            # Clear demo executor old demos
            demo_executor.cleanup_old_demos(max_age_hours=0)  # Clear all
            
            # Clear config cache
            self._config_cache.clear()
            self._load_all_configs()
            
            logger.info("System caches cleared")
            return {
                "success": True,
                "message": "System caches cleared successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to clear cache: {str(e)}"
            }
    
    def _export_diagnostics(self, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Export system diagnostics."""
        try:
            diagnostics = {
                "timestamp": datetime.now().isoformat(),
                "system_health": self.get_system_health().model_dump(),
                "system_metrics": self.get_system_metrics().model_dump(),
                "active_demos": len(demo_executor.list_demos()),
                "configuration": self._config_cache
            }
            
            return {
                "success": True,
                "message": "Diagnostics exported successfully",
                "data": diagnostics
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to export diagnostics: {str(e)}"
            }
    
    def _view_logs(self, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """View system logs."""
        try:
            log_lines = parameters.get("lines", 50) if parameters else 50
            
            # Read last N lines of log file
            log_file = Path("logs/api.log")
            if not log_file.exists():
                return {
                    "success": False,
                    "message": "Log file not found"
                }
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-log_lines:] if len(lines) > log_lines else lines
            
            return {
                "success": True,
                "message": f"Retrieved last {len(recent_lines)} log lines",
                "data": {
                    "lines": [line.strip() for line in recent_lines],
                    "total_lines": len(lines)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to read logs: {str(e)}"
            }


