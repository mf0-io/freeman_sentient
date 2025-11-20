"""Configuration loader for YAML-based persona configs

This module provides utilities for loading and validating persona configurations
from YAML files, including support for environment variable substitution and
default values.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigLoadError(Exception):
    """Raised when configuration loading fails"""
    pass


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


def load_persona_config(file_path: str) -> Dict[str, Any]:
    """Load and validate a persona configuration from a YAML file

    This function loads a YAML configuration file and performs:
    - Environment variable substitution (${VAR_NAME} or $VAR_NAME)
    - YAML structure validation
    - Required fields validation

    Args:
        file_path: Path to the YAML configuration file

    Returns:
        Dictionary containing the parsed and validated configuration

    Raises:
        ConfigLoadError: If the file cannot be loaded
        ConfigValidationError: If the configuration is invalid

    Example:
        >>> config = load_persona_config('config/freeman.yaml')
        >>> print(config['id'])
        'freeman'
    """
    # Validate file path
    if not file_path:
        raise ConfigLoadError("Configuration file path is required")

    path = Path(file_path)
    if not path.exists():
        raise ConfigLoadError(f"Configuration file not found: {file_path}")

    if not path.is_file():
        raise ConfigLoadError(f"Path is not a file: {file_path}")

    # Load YAML file
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigLoadError(f"Failed to parse YAML file {file_path}: {e}")
    except Exception as e:
        raise ConfigLoadError(f"Failed to read configuration file {file_path}: {e}")

    if config is None:
        raise ConfigLoadError(f"Configuration file is empty: {file_path}")

    if not isinstance(config, dict):
        raise ConfigLoadError(f"Configuration must be a dictionary, got {type(config).__name__}")

    # Substitute environment variables
    config = _substitute_env_vars(config)

    # Validate configuration structure
    _validate_config(config, file_path)

    return config


def _substitute_env_vars(config: Any) -> Any:
    """Recursively substitute environment variables in configuration values

    Supports both ${VAR_NAME} and $VAR_NAME syntax.
    If environment variable is not found, the placeholder is left unchanged.

    Args:
        config: Configuration value (can be dict, list, str, or any type)

    Returns:
        Configuration with environment variables substituted
    """
    if isinstance(config, dict):
        return {key: _substitute_env_vars(value) for key, value in config.items()}

    elif isinstance(config, list):
        return [_substitute_env_vars(item) for item in config]

    elif isinstance(config, str):
        # Pattern to match ${VAR_NAME} or $VAR_NAME
        # First try ${VAR_NAME} format
        def replace_braced(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        # Replace ${VAR_NAME} patterns
        result = re.sub(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}', replace_braced, config)

        # Replace standalone $VAR_NAME patterns (not followed by more word chars)
        def replace_unbraced(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        result = re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)(?![A-Za-z0-9_])', replace_unbraced, result)

        return result

    else:
        return config


def _validate_config(config: Dict[str, Any], file_path: str) -> None:
    """Validate that the configuration has required fields and valid structure

    Args:
        config: Configuration dictionary to validate
        file_path: Path to the config file (for error messages)

    Raises:
        ConfigValidationError: If validation fails
    """
    # Required top-level fields
    required_fields = ['id', 'name']

    for field in required_fields:
        if field not in config:
            raise ConfigValidationError(
                f"Missing required field '{field}' in configuration file {file_path}"
            )

        if not config[field]:
            raise ConfigValidationError(
                f"Required field '{field}' cannot be empty in configuration file {file_path}"
            )

    # Validate id format (lowercase alphanumeric with hyphens/underscores)
    persona_id = config['id']
    if not isinstance(persona_id, str):
        raise ConfigValidationError(
            f"Field 'id' must be a string in configuration file {file_path}"
        )

    if not re.match(r'^[a-z0-9_-]+$', persona_id):
        raise ConfigValidationError(
            f"Field 'id' must contain only lowercase letters, numbers, hyphens, and underscores in {file_path}"
        )

    # Validate name
    if not isinstance(config['name'], str):
        raise ConfigValidationError(
            f"Field 'name' must be a string in configuration file {file_path}"
        )

    # Validate optional sections are dictionaries if present
    optional_dict_sections = [
        'personality', 'memory', 'agents', 'platforms',
        'llm', 'behavior', 'philosophy'
    ]

    for section in optional_dict_sections:
        if section in config and config[section] is not None:
            if not isinstance(config[section], dict):
                raise ConfigValidationError(
                    f"Section '{section}' must be a dictionary in configuration file {file_path}"
                )


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries, with override taking precedence

    This performs a deep merge where:
    - Nested dictionaries are merged recursively
    - Lists are replaced (not merged)
    - Scalar values from override replace base values

    Args:
        base_config: Base configuration dictionary
        override_config: Configuration to override base with

    Returns:
        Merged configuration dictionary

    Example:
        >>> base = {'a': 1, 'b': {'c': 2}}
        >>> override = {'b': {'d': 3}}
        >>> merge_configs(base, override)
        {'a': 1, 'b': {'c': 2, 'd': 3}}
    """
    result = base_config.copy()

    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = merge_configs(result[key], value)
        else:
            # Override with new value
            result[key] = value

    return result


def load_persona_config_with_defaults(
    file_path: str,
    defaults_path: Optional[str] = None
) -> Dict[str, Any]:
    """Load a persona configuration with optional default values

    If defaults_path is provided, loads defaults first, then merges
    the main configuration on top.

    Args:
        file_path: Path to the main YAML configuration file
        defaults_path: Optional path to defaults YAML file

    Returns:
        Dictionary containing the merged configuration

    Raises:
        ConfigLoadError: If files cannot be loaded
        ConfigValidationError: If configuration is invalid
    """
    # Load defaults if provided
    if defaults_path:
        base_config = load_persona_config(defaults_path)
    else:
        base_config = {}

    # Load main config
    main_config = load_persona_config(file_path)

    # Merge configurations
    if base_config:
        return merge_configs(base_config, main_config)
    else:
        return main_config
