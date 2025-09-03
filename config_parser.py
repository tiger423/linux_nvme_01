"""
Configuration Parser - YAML Configuration Handler
Handles test configuration loading, validation, and device type management
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigParser:
    """Handles configuration file parsing and validation"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.default_config = self._get_default_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with defaults"""
        
        # Start with default configuration
        config = self.default_config.copy()
        
        # Load from file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = yaml.safe_load(f)
                
                if file_config:
                    # Merge file config with defaults
                    config.update(file_config)
                    
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML configuration file: {e}")
            except Exception as e:
                raise ValueError(f"Error reading configuration file: {e}")
        else:
            print(f"Configuration file {self.config_file} not found, using defaults")
        
        # Validate configuration
        self._validate_config(config)
        
        # Apply device type specific settings
        config = self._apply_device_type_settings(config)
        
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration matching test specification"""
        
        return {
            # Core test parameters from specification
            'device': '/dev/nvme0n1',
            'device_type': 'bravo',
            'runmode': 'prod',
            'description': 'linux_nvme_information_cmd test',
            'quid': 'nvme_info_qual_2024',
            
            # Command execution parameters
            'command_timeout': 30,
            'retry_attempts': 1,
            'retry_delay': 2,
            
            # Logging configuration
            'log_level': 'INFO',
            'output_dir': './logs',
            'save_raw_outputs': True,
            'include_timestamps': True,
            
            # Pass/fail criteria settings
            'allow_thermal_warnings': True,
            'max_acceptable_media_errors': 0,
            'require_all_commands_success': True,
            
            # Device type specific expectations (will be updated by _apply_device_type_settings)
            'expected_pcie': {
                'width': 4,
                'speed': 3
            },
            'smart_thresholds': {
                'max_temperature': 70,
                'min_available_spare': 10,
                'max_percent_used': 90
            }
        }
    
    def _apply_device_type_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply device type specific configuration settings"""
        
        device_type = config.get('device_type', 'bravo')
        
        # Device type specific configurations
        device_settings = {
            'bravo': {
                'expected_pcie': {
                    'width': 4,      # x4 lanes
                    'speed': 3       # Gen3 (8.0 GT/s)
                },
                'smart_thresholds': {
                    'max_temperature': 70,
                    'min_available_spare': 10,
                    'max_percent_used': 80
                },
                'command_timeout': 30,
                'expected_namespaces': 1
            },
            'delta': {
                'expected_pcie': {
                    'width': 8,      # x8 lanes  
                    'speed': 4       # Gen4 (16.0 GT/s)
                },
                'smart_thresholds': {
                    'max_temperature': 75,
                    'min_available_spare': 10,
                    'max_percent_used': 85
                },
                'command_timeout': 25,
                'expected_namespaces': 1
            },
            'echo': {
                'expected_pcie': {
                    'width': 4,      # x4 lanes
                    'speed': 4       # Gen4 (16.0 GT/s) 
                },
                'smart_thresholds': {
                    'max_temperature': 80,
                    'min_available_spare': 15,
                    'max_percent_used': 90
                },
                'command_timeout': 35,
                'expected_namespaces': 2
            },
            'compete': {
                'expected_pcie': {
                    'width': 16,     # x16 lanes
                    'speed': 4       # Gen4 (16.0 GT/s)
                },
                'smart_thresholds': {
                    'max_temperature': 85,
                    'min_available_spare': 20,
                    'max_percent_used': 95
                },
                'command_timeout': 20,
                'expected_namespaces': 4
            }
        }
        
        # Apply device specific settings
        if device_type in device_settings:
            device_config = device_settings[device_type]
            
            # Update PCIe expectations
            config['expected_pcie'].update(device_config['expected_pcie'])
            
            # Update SMART thresholds
            config['smart_thresholds'].update(device_config['smart_thresholds'])
            
            # Update other device-specific settings
            config['command_timeout'] = device_config['command_timeout']
            config['expected_namespaces'] = device_config['expected_namespaces']
            
        else:
            print(f"Warning: Unknown device type '{device_type}', using bravo defaults")
        
        return config
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration parameters"""
        
        # Required fields validation
        required_fields = ['device', 'device_type', 'runmode']
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required configuration field: {field}")
        
        # Device path validation
        device_path = config['device']
        if not isinstance(device_path, str) or not device_path.startswith('/dev/nvme'):
            raise ValueError(f"Invalid device path: {device_path}")
        
        # Device type validation
        valid_device_types = ['bravo', 'delta', 'echo', 'compete']
        device_type = config['device_type']
        if device_type not in valid_device_types:
            raise ValueError(f"Invalid device_type: {device_type}. Must be one of: {valid_device_types}")
        
        # Runmode validation
        valid_runmodes = ['prod', 'debug', 'dryrun']
        runmode = config['runmode']
        if runmode not in valid_runmodes:
            raise ValueError(f"Invalid runmode: {runmode}. Must be one of: {valid_runmodes}")
        
        # Timeout validation
        timeout = config.get('command_timeout', 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 300:
            raise ValueError(f"Invalid command_timeout: {timeout}. Must be between 1 and 300 seconds")
        
        # Log level validation
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        log_level = config.get('log_level', 'INFO')
        if log_level not in valid_log_levels:
            raise ValueError(f"Invalid log_level: {log_level}. Must be one of: {valid_log_levels}")
        
        # Output directory validation
        output_dir = config.get('output_dir', './logs')
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Cannot create output directory {output_dir}: {e}")
    
    def save_config(self, config: Dict[str, Any], output_file: Optional[str] = None) -> None:
        """Save configuration to YAML file"""
        
        if output_file is None:
            output_file = self.config_file
        
        try:
            with open(output_file, 'w') as f:
                yaml.safe_dump(config, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise ValueError(f"Error saving configuration to {output_file}: {e}")
    
    def get_device_info(self, device_type: str) -> Dict[str, Any]:
        """Get device type information"""
        
        device_info = {
            'bravo': {
                'name': 'Bravo Series Enterprise SSD',
                'interface': 'PCIe Gen3 x4',
                'capacity_range': '960GB - 7.68TB',
                'endurance': 'High endurance enterprise',
                'use_case': 'General enterprise workloads'
            },
            'delta': {
                'name': 'Delta Series High-Performance SSD', 
                'interface': 'PCIe Gen4 x8',
                'capacity_range': '1.92TB - 15.36TB',
                'endurance': 'Ultra-high endurance',
                'use_case': 'High-performance computing'
            },
            'echo': {
                'name': 'Echo Series Multi-Namespace SSD',
                'interface': 'PCIe Gen4 x4', 
                'capacity_range': '480GB - 3.84TB',
                'endurance': 'Standard enterprise',
                'use_case': 'Multi-tenant environments'
            },
            'compete': {
                'name': 'Compete Series Flagship SSD',
                'interface': 'PCIe Gen4 x16',
                'capacity_range': '3.84TB - 30.72TB', 
                'endurance': 'Maximum endurance',
                'use_case': 'Mission-critical applications'
            }
        }
        
        return device_info.get(device_type, {})
    
    def validate_runtime_config(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Validate runtime configuration and return warnings"""
        
        warnings = {}
        
        # Check if device file exists
        device_path = config.get('device')
        if device_path and not os.path.exists(device_path):
            warnings['device_not_found'] = f"Device file {device_path} not found"
        
        # Check permissions for device access
        if device_path and os.path.exists(device_path):
            if not os.access(device_path, os.R_OK):
                warnings['device_permission'] = f"No read permission for {device_path}"
        
        # Check if running with sufficient privileges
        if os.geteuid() != 0:
            warnings['privilege'] = "Not running as root - some commands may fail"
        
        # Check output directory permissions
        output_dir = config.get('output_dir')
        if output_dir:
            try:
                test_file = os.path.join(output_dir, '.permission_test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception:
                warnings['output_dir'] = f"No write permission for output directory {output_dir}"
        
        return warnings
    
    @staticmethod
    def create_sample_config(filename: str = 'sample_config.yaml') -> None:
        """Create a sample configuration file"""
        
        sample_config = {
            'device': '/dev/nvme0n1',
            'device_type': 'bravo',
            'runmode': 'prod',
            'description': 'NVMe Information Command Test',
            'quid': 'nvme_info_qualification_2024',
            
            'command_timeout': 30,
            'retry_attempts': 1,
            
            'log_level': 'INFO',
            'output_dir': './logs',
            'save_raw_outputs': True,
            
            'allow_thermal_warnings': True,
            'max_acceptable_media_errors': 0,
            
            'expected_pcie': {
                'width': 4,
                'speed': 3
            },
            
            'smart_thresholds': {
                'max_temperature': 70,
                'min_available_spare': 10,
                'max_percent_used': 80
            }
        }
        
        with open(filename, 'w') as f:
            yaml.safe_dump(sample_config, f, default_flow_style=False, indent=2)
        
        print(f"Sample configuration created: {filename}")