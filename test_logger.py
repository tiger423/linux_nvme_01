"""
Test Logger - Comprehensive Logging and Result Output
Handles structured logging, raw output preservation, and TDS integration
"""

import logging
import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class TestLogger:
    """Comprehensive test logging system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config.get('output_dir', './logs'))
        self.test_start_time = None
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logging
        self._setup_logging()
        
        # Initialize result storage
        self.test_results = {}
        self.raw_command_outputs = {}
        
    def _setup_logging(self) -> None:
        """Setup structured logging with file and console handlers"""
        
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        
        # Create logger
        self.logger = logging.getLogger('nvme_test')
        self.logger.setLevel(log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # File handler for detailed logs
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.output_dir / f'nvme_test_{timestamp}.log'
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for user feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        self.log_file_path = log_file
        
    def log_test_start(self, config: Dict[str, Any]) -> None:
        """Log test execution start with configuration details"""
        
        self.test_start_time = datetime.now()
        
        self.logger.info("=" * 80)
        self.logger.info("NVMe Information Command Test - EXECUTION START")
        self.logger.info("=" * 80)
        
        # Log test configuration
        self.logger.info(f"Test Start Time: {self.test_start_time.isoformat()}")
        self.logger.info(f"Device: {config['device']}")
        self.logger.info(f"Device Type: {config['device_type']}")
        self.logger.info(f"Run Mode: {config['runmode']}")
        self.logger.info(f"Qualification ID: {config.get('quid', 'N/A')}")
        self.logger.info(f"Command Timeout: {config.get('command_timeout', 30)} seconds")
        
        # Log expected parameters
        if 'expected_pcie' in config:
            pcie = config['expected_pcie']
            self.logger.info(f"Expected PCIe: x{pcie['width']} Gen{pcie['speed']}")
        
        # Log environment information
        self.logger.info(f"Log Output Directory: {self.output_dir}")
        self.logger.info(f"Python Executable: {os.sys.executable}")
        self.logger.info(f"Working Directory: {os.getcwd()}")
        
        self.logger.info("-" * 80)
    
    def log_test_completion(self, test_result) -> None:
        """Log test completion with comprehensive results"""
        
        test_end_time = datetime.now()
        execution_duration = test_end_time - self.test_start_time if self.test_start_time else None
        
        self.logger.info("-" * 80)
        self.logger.info("NVMe Information Command Test - EXECUTION COMPLETE")
        self.logger.info("-" * 80)
        
        self.logger.info(f"Test End Time: {test_end_time.isoformat()}")
        if execution_duration:
            self.logger.info(f"Total Execution Duration: {execution_duration}")
        
        # Log test statistics
        self.logger.info(f"Overall Result: {test_result.overall_status}")
        self.logger.info(f"Commands Executed: {test_result.commands_executed}")
        self.logger.info(f"Commands Passed: {test_result.commands_passed}")
        self.logger.info(f"Commands Failed: {test_result.commands_failed}")
        
        # Log failure details
        if test_result.failure_reasons:
            self.logger.error("FAILURE REASONS:")
            for reason in test_result.failure_reasons:
                self.logger.error(f"  - {reason}")
        
        # Save comprehensive results
        self._save_json_results(test_result, test_end_time)
        self._save_csv_summary(test_result, test_end_time)
        
        if self.config.get('save_raw_outputs', True):
            self._save_raw_outputs(test_result.raw_outputs)
        
        # Save TDS integration file
        self._save_tds_results(test_result, test_end_time)
        
        self.logger.info(f"Results saved to: {self.output_dir}")
        self.logger.info("=" * 80)
    
    def log_command_execution(self, command_name: str, result) -> None:
        """Log individual command execution details"""
        
        if result.success:
            self.logger.info(f"✓ {command_name} completed successfully ({result.execution_time:.2f}s)")
            self.logger.debug(f"Command: {result.command}")
        else:
            self.logger.error(f"✗ {command_name} failed ({result.execution_time:.2f}s)")
            self.logger.error(f"Command: {result.command}")
            self.logger.error(f"Error: {result.error_message}")
            if result.raw_output:
                self.logger.debug(f"Raw Output: {result.raw_output[:500]}...")
    
    def _save_json_results(self, test_result, end_time: datetime) -> None:
        """Save comprehensive test results in JSON format"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = self.output_dir / f'nvme_test_results_{timestamp}.json'
        
        results_data = {
            'test_metadata': {
                'test_name': 'linux_nvme_01_information_cmd',
                'test_version': '1.0.0',
                'start_time': self.test_start_time.isoformat() if self.test_start_time else None,
                'end_time': end_time.isoformat(),
                'execution_time_seconds': test_result.execution_time,
                'quid': self.config.get('quid'),
                'device': self.config.get('device'),
                'device_type': self.config.get('device_type'),
                'runmode': self.config.get('runmode')
            },
            'test_results': {
                'overall_status': test_result.overall_status,
                'commands_executed': test_result.commands_executed,
                'commands_passed': test_result.commands_passed,
                'commands_failed': test_result.commands_failed,
                'failure_reasons': test_result.failure_reasons
            },
            'detailed_analysis': test_result.detailed_results,
            'configuration': self.config
        }
        
        with open(json_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        self.logger.debug(f"JSON results saved: {json_file}")
    
    def _save_csv_summary(self, test_result, end_time: datetime) -> None:
        """Save test summary in CSV format for batch processing"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = self.output_dir / f'nvme_test_summary_{timestamp}.csv'
        
        summary_data = {
            'timestamp': end_time.isoformat(),
            'device': self.config.get('device'),
            'device_type': self.config.get('device_type'),
            'quid': self.config.get('quid'),
            'overall_status': test_result.overall_status,
            'execution_time': test_result.execution_time,
            'commands_executed': test_result.commands_executed,
            'commands_passed': test_result.commands_passed,
            'commands_failed': test_result.commands_failed,
            'failure_count': len(test_result.failure_reasons),
            'failure_reasons': '; '.join(test_result.failure_reasons) if test_result.failure_reasons else '',
        }
        
        # Add detailed analysis summary
        if 'smart_analysis' in test_result.detailed_results:
            smart = test_result.detailed_results['smart_analysis']
            summary_data['smart_media_errors'] = smart.get('media_error_count', 0)
            summary_data['smart_critical_warnings'] = smart.get('failed', False)
        
        if 'pcie_analysis' in test_result.detailed_results:
            pcie = test_result.detailed_results['pcie_analysis']
            summary_data['pcie_width'] = pcie.get('actual_width', '')
            summary_data['pcie_speed'] = pcie.get('actual_speed', '')
            summary_data['pcie_validation'] = not pcie.get('failed', True)
        
        # Write CSV
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=summary_data.keys())
            writer.writeheader()
            writer.writerow(summary_data)
        
        self.logger.debug(f"CSV summary saved: {csv_file}")
    
    def _save_raw_outputs(self, raw_outputs: Dict[str, str]) -> None:
        """Save raw command outputs for debugging"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        raw_dir = self.output_dir / f'raw_outputs_{timestamp}'
        raw_dir.mkdir(exist_ok=True)
        
        for command_name, output in raw_outputs.items():
            output_file = raw_dir / f'{command_name}_output.txt'
            
            with open(output_file, 'w') as f:
                f.write(f"Command: {command_name}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n")
                f.write(output)
                f.write("\n" + "=" * 80 + "\n")
        
        self.logger.debug(f"Raw outputs saved: {raw_dir}")
    
    def _save_tds_results(self, test_result, end_time: datetime) -> None:
        """Save results in TDS (Test Data System) integration format"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        tds_file = self.output_dir / f'tds_integration_{timestamp}.json'
        
        tds_data = {
            'qualification_id': self.config.get('quid'),
            'test_suite': 'linux_nvme_01',
            'test_case': 'nvme_information_cmd',
            'device_under_test': {
                'device_path': self.config.get('device'),
                'device_type': self.config.get('device_type'),
                'description': self.config.get('description', '')
            },
            'execution_info': {
                'start_time': self.test_start_time.isoformat() if self.test_start_time else None,
                'end_time': end_time.isoformat(),
                'duration_seconds': test_result.execution_time,
                'runmode': self.config.get('runmode')
            },
            'test_verdict': {
                'overall_result': test_result.overall_status,
                'pass_criteria_met': test_result.overall_status == 'PASS',
                'failure_reasons': test_result.failure_reasons
            },
            'metrics': {
                'commands_total': test_result.commands_executed,
                'commands_passed': test_result.commands_passed,
                'commands_failed': test_result.commands_failed,
                'success_rate_percent': (test_result.commands_passed / test_result.commands_executed * 100) if test_result.commands_executed > 0 else 0
            },
            'deliverables': {
                'log_files': [str(self.log_file_path)],
                'result_files': [str(f) for f in self.output_dir.glob('*') if f.is_file()],
                'raw_outputs_available': self.config.get('save_raw_outputs', True)
            }
        }
        
        with open(tds_file, 'w') as f:
            json.dump(tds_data, f, indent=2, default=str)
        
        self.logger.debug(f"TDS integration file saved: {tds_file}")
    
    def info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(message)
    
    def debug(self, message: str) -> None:
        """Log debug message"""
        self.logger.debug(message)
    
    def warning(self, message: str) -> None:
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message"""
        self.logger.error(message)
    
    def get_log_file_path(self) -> str:
        """Return path to current log file"""
        return str(self.log_file_path)
    
    def create_test_report(self, test_result) -> str:
        """Create formatted test report"""
        
        report_lines = []
        report_lines.append("NVMe Information Command Test Report")
        report_lines.append("=" * 50)
        report_lines.append("")
        
        # Test summary
        report_lines.append("TEST SUMMARY:")
        report_lines.append(f"  Device: {self.config.get('device')}")
        report_lines.append(f"  Device Type: {self.config.get('device_type')}")
        report_lines.append(f"  Overall Result: {test_result.overall_status}")
        report_lines.append(f"  Execution Time: {test_result.execution_time:.2f} seconds")
        report_lines.append("")
        
        # Command results
        report_lines.append("COMMAND EXECUTION SUMMARY:")
        report_lines.append(f"  Total Commands: {test_result.commands_executed}")
        report_lines.append(f"  Passed: {test_result.commands_passed}")
        report_lines.append(f"  Failed: {test_result.commands_failed}")
        report_lines.append("")
        
        # Failure analysis
        if test_result.failure_reasons:
            report_lines.append("FAILURE ANALYSIS:")
            for reason in test_result.failure_reasons:
                report_lines.append(f"  • {reason}")
            report_lines.append("")
        
        # Detailed results
        if test_result.detailed_results:
            report_lines.append("DETAILED ANALYSIS:")
            
            for category, analysis in test_result.detailed_results.items():
                report_lines.append(f"  {category.upper()}:")
                if isinstance(analysis, dict):
                    for key, value in analysis.items():
                        report_lines.append(f"    {key}: {value}")
                report_lines.append("")
        
        return "\n".join(report_lines)