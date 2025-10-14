# -*- coding: utf-8 -*-
"""
Configuration Settings Module

This module handles all configuration settings for the EDA application,
including API keys, paths, and other application settings.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

class Settings:
    """
    Configuration settings class for the EDA application
    """

    def __init__(self):
        """Initialize settings with default values"""
        self.base_dir = Path(__file__).parent.parent.parent
        self.load_settings()

    def load_settings(self):
        """Load all configuration settings"""
        # API Configuration
        self.google_api_key = os.getenv('GOOGLE_API_KEY', '')

        # Model Configuration
        self.gemini_model = 'gemini-2.0-flash-exp'
        self.temperature = 0.1
        self.max_tokens = 8192

        # Directory Configuration
        self.charts_dir = "charts"
        self.reports_dir = "reports"
        self.data_dir = "data"
        self.logs_dir = "logs"

        # File Configuration
        self.supported_formats = ['.csv', '.xlsx', '.xls']
        self.max_file_size = 100 * 1024 * 1024  # 100MB

        # Visualization Configuration
        self.default_figure_size = (12, 8)
        self.default_dpi = 300
        self.chart_style = 'seaborn-v0_8'

        # Analysis Configuration
        self.correlation_threshold = 0.5
        self.outlier_method = 'IQR'
        self.outlier_multiplier = 1.5
        self.max_categorical_unique = 50

        # Memory Configuration
        self.max_memory_usage = 0.8  # 80% of available memory
        self.chunk_size = 10000

        # UI Configuration
        self.language = 'pt_BR'
        self.timezone = 'America/Sao_Paulo'

    def get_output_path(self, output_type: str, filename: str = None) -> str:
        """
        Get the full output path for a given type and filename

        Args:
            output_type: Type of output ('charts', 'reports', 'data', 'logs')
            filename: Optional filename

        Returns:
            str: Full path to the output file/directory
        """
        type_dirs = {
            'charts': self.charts_dir,
            'reports': self.reports_dir,
            'data': self.data_dir,
            'logs': self.logs_dir
        }

        if output_type not in type_dirs:
            raise ValueError(f"Invalid output type: {output_type}")

        output_dir = self.base_dir / type_dirs[output_type]
        output_dir.mkdir(exist_ok=True)

        if filename:
            return str(output_dir / filename)
        return str(output_dir)

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate Google API key format

        Args:
            api_key: The API key to validate

        Returns:
            bool: True if key appears valid, False otherwise
        """
        if not api_key:
            return False

        # Basic validation - Google API keys are typically 39 characters
        if len(api_key) < 30:
            return False

        # Should start with specific patterns for Google API keys
        valid_prefixes = ['AIza', 'GOOG']
        if not any(api_key.startswith(prefix) for prefix in valid_prefixes):
            return False

        return True

    def set_api_key(self, api_key: str) -> bool:
        """
        Set and validate the Google API key

        Args:
            api_key: The API key to set

        Returns:
            bool: True if key was set successfully, False otherwise
        """
        if self.validate_api_key(api_key):
            self.google_api_key = api_key
            os.environ['GOOGLE_API_KEY'] = api_key
            return True
        return False

    def get_model_config(self) -> Dict[str, Any]:
        """
        Get model configuration for LLM initialization

        Returns:
            Dict with model configuration parameters
        """
        return {
            'model': self.gemini_model,
            'temperature': self.temperature,
            'max_output_tokens': self.max_tokens,
            'google_api_key': self.google_api_key
        }

    def get_visualization_config(self) -> Dict[str, Any]:
        """
        Get visualization configuration

        Returns:
            Dict with visualization settings
        """
        return {
            'figure_size': self.default_figure_size,
            'dpi': self.default_dpi,
            'style': self.chart_style,
            'output_dir': self.get_output_path('charts')
        }

    def get_analysis_config(self) -> Dict[str, Any]:
        """
        Get analysis configuration

        Returns:
            Dict with analysis settings
        """
        return {
            'correlation_threshold': self.correlation_threshold,
            'outlier_method': self.outlier_method,
            'outlier_multiplier': self.outlier_multiplier,
            'max_categorical_unique': self.max_categorical_unique
        }

    def create_directories(self):
        """Create all necessary directories"""
        directories = [
            self.charts_dir,
            self.reports_dir,
            self.data_dir,
            self.logs_dir
        ]

        for directory in directories:
            full_path = self.base_dir / directory
            full_path.mkdir(exist_ok=True)

    def get_file_config(self) -> Dict[str, Any]:
        """
        Get file handling configuration

        Returns:
            Dict with file settings
        """
        return {
            'supported_formats': self.supported_formats,
            'max_file_size': self.max_file_size,
            'chunk_size': self.chunk_size
        }

    def save_to_env_file(self, env_path: str = '.env'):
        """
        Save current settings to .env file

        Args:
            env_path: Path to the .env file
        """
        env_content = f"""# EDA Application Configuration
GOOGLE_API_KEY={self.google_api_key}

# Model Configuration
GEMINI_MODEL={self.gemini_model}
TEMPERATURE={self.temperature}
MAX_TOKENS={self.max_tokens}

# Directory Configuration
CHARTS_DIR={self.charts_dir}
REPORTS_DIR={self.reports_dir}
DATA_DIR={self.data_dir}
LOGS_DIR={self.logs_dir}

# Analysis Configuration
CORRELATION_THRESHOLD={self.correlation_threshold}
OUTLIER_METHOD={self.outlier_method}
OUTLIER_MULTIPLIER={self.outlier_multiplier}

# UI Configuration
LANGUAGE={self.language}
TIMEZONE={self.timezone}
"""

        env_file_path = self.base_dir / env_path
        with open(env_file_path, 'w', encoding='utf-8') as f:
            f.write(env_content)

    def load_from_env_file(self, env_path: str = '.env'):
        """
        Load settings from .env file

        Args:
            env_path: Path to the .env file
        """
        from dotenv import load_dotenv

        env_file_path = self.base_dir / env_path
        if env_file_path.exists():
            load_dotenv(env_file_path)
            self.load_settings()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to dictionary

        Returns:
            Dict with all settings
        """
        return {
            'api': {
                'google_api_key': self.google_api_key,
                'gemini_model': self.gemini_model,
                'temperature': self.temperature,
                'max_tokens': self.max_tokens
            },
            'directories': {
                'charts_dir': self.charts_dir,
                'reports_dir': self.reports_dir,
                'data_dir': self.data_dir,
                'logs_dir': self.logs_dir
            },
            'files': {
                'supported_formats': self.supported_formats,
                'max_file_size': self.max_file_size,
                'chunk_size': self.chunk_size
            },
            'visualization': {
                'figure_size': self.default_figure_size,
                'dpi': self.default_dpi,
                'style': self.chart_style
            },
            'analysis': {
                'correlation_threshold': self.correlation_threshold,
                'outlier_method': self.outlier_method,
                'outlier_multiplier': self.outlier_multiplier,
                'max_categorical_unique': self.max_categorical_unique
            },
            'ui': {
                'language': self.language,
                'timezone': self.timezone
            }
        }

    def __str__(self) -> str:
        """String representation of settings"""
        return f"EDA Settings: {self.gemini_model} model, API key: {'Set' if self.google_api_key else 'Not set'}"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance

    Returns:
        Settings: The global settings object
    """
    return settings


def configure_api_key(api_key: str) -> bool:
    """
    Configure the Google API key globally

    Args:
        api_key: The Google API key

    Returns:
        bool: True if configured successfully, False otherwise
    """
    return settings.set_api_key(api_key)


def setup_directories():
    """Setup all required directories"""
    settings.create_directories()


def get_chart_path(filename: str = None) -> str:
    """
    Get path for chart files

    Args:
        filename: Optional filename

    Returns:
        str: Path to charts directory or specific file
    """
    return settings.get_output_path('charts', filename)


def get_report_path(filename: str = None) -> str:
    """
    Get path for report files

    Args:
        filename: Optional filename

    Returns:
        str: Path to reports directory or specific file
    """
    return settings.get_output_path('reports', filename)


def get_data_path(filename: str = None) -> str:
    """
    Get path for data files

    Args:
        filename: Optional filename

    Returns:
        str: Path to data directory or specific file
    """
    return settings.get_output_path('data', filename)


# Configuration for different environments
class DevelopmentSettings(Settings):
    """Development environment settings"""

    def __init__(self):
        super().__init__()
        self.temperature = 0.2  # More creative responses in development
        self.max_tokens = 4096  # Lower token limit for testing


class ProductionSettings(Settings):
    """Production environment settings"""

    def __init__(self):
        super().__init__()
        self.temperature = 0.1  # More consistent responses in production
        self.max_tokens = 8192  # Higher token limit for production


def get_environment_settings(environment: str = 'production') -> Settings:
    """
    Get settings for specific environment

    Args:
        environment: Environment name ('development' or 'production')

    Returns:
        Settings: Environment-specific settings object
    """
    if environment.lower() == 'development':
        return DevelopmentSettings()
    else:
        return ProductionSettings()