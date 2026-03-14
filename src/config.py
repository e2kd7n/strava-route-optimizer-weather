"""
Configuration management module.

Handles loading and parsing of configuration files and environment variables.

Copyright (c) 2024-2026 e2kd7n
Licensed under the MIT License - see LICENSE file for details.

This software requires valid Strava API credentials to function.
Unauthorized use, reproduction, or distribution is prohibited.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class Config:
    """Configuration manager for the application."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file and environment variables.
        
        Returns:
            Dictionary containing configuration values
        """
        # Load environment variables
        load_dotenv()
        
        # Load YAML configuration
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Replace environment variable placeholders
        config = self._replace_env_vars(config)
        
        return config
    
    def _replace_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively replace ${VAR_NAME} placeholders with environment variables.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with environment variables replaced
        """
        if isinstance(config, dict):
            return {k: self._replace_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._replace_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
            var_name = config[2:-1]
            value = os.getenv(var_name)
            if value is None:
                raise ValueError(f"Environment variable {var_name} not found")
            return value
        else:
            return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key using dot notation.
        
        Args:
            key: Configuration key (e.g., 'strava.client_id')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to configuration."""
        return self.config[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in configuration."""
        return key in self.config


def load_config(config_path: str = "config/config.yaml") -> Config:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Config object
    """
    return Config(config_path)

# Made with Bob
