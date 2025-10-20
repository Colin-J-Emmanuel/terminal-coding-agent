"""
Configuration management for the coding agent.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """
    Configuration manager that loads settings from:
    1. Environment variables (.env file)
    2. YAML configuration file (config.yaml)
    3. Default values
    """
    
    def __init__(self, config_file: str = "config.yaml"):
        # Load environment variables
        load_dotenv()
        
        # Load YAML config
        self.config_data = self._load_yaml(config_file)
        
        # Apply environment variable overrides
        self._apply_env_overrides()
    
    def _load_yaml(self, config_file: str) -> Dict:
        """Load configuration from YAML file."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            print(f"Warning: Config file {config_file} not found. Using defaults.")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading config file: {e}")
            return {}
    
    def _apply_env_overrides(self):
        """
        Apply environment variable overrides to config.
        
        Environment variables can override config values using dot notation:
        AGENT_MODEL -> llm.model
        EXECUTION_TIMEOUT -> tools.code_execution.timeout_seconds
        """
        env_mappings = {
            "AGENT_MODEL": "llm.model",
            "AGENT_MAX_TOKENS": "llm.max_tokens",
            "AGENT_TEMPERATURE": "llm.temperature",
            "EXECUTION_TIMEOUT": "tools.code_execution.timeout_seconds",
            "EXECUTION_MAX_MEMORY_MB": "tools.code_execution.max_memory_mb",
            "EXECUTION_MAX_CPU_TIME": "tools.code_execution.max_cpu_time_seconds",
            "WORKING_DIRECTORY": "working_directory",
            "LOG_LEVEL": "logging.level",
            "LOG_FILE": "logging.file",
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string to appropriate type
                value = self._convert_type(value)
                self.set(config_path, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Examples:
            config.get("llm.model")
            config.get("tools.code_execution.timeout_seconds", 10)
        
        Args:
            key: Configuration key in dot notation
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self.config_data
        
        # Navigate to the nested dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def _convert_type(self, value: str) -> Any:
        """
        Convert string value to appropriate type.
        
        Args:
            value: String value from environment variable
            
        Returns:
            Converted value (int, float, bool, or str)
        """
        # Try boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def get_all(self) -> Dict:
        """Get all configuration as a dictionary."""
        return self.config_data.copy()
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        required_keys = [
            "llm.model",
            "llm.max_tokens",
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                print(f"Error: Required configuration key '{key}' is missing")
                return False
        
        # Validate API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("Error: ANTHROPIC_API_KEY environment variable is not set")
            return False
        
        return True
    
    def __repr__(self) -> str:
        """String representation of config (without sensitive data)."""
        safe_config = self.config_data.copy()
        
        # Remove sensitive keys
        if 'api_keys' in safe_config:
            safe_config['api_keys'] = '***'
        
        return f"Config({safe_config})"


def load_config(config_file: str = "config.yaml") -> Config:
    """
    Convenience function to load configuration.
    
    Args:
        config_file: Path to YAML configuration file
        
    Returns:
        Config instance
    """
    config = Config(config_file)
    
    if not config.validate():
        raise ValueError("Invalid configuration. Please check your config.yaml and .env files.")
    
    return config