"""
NVMe Test Executor - Core Test Execution Engine
Executes the 8-command test sequence for linux_nvme_01
"""

import time
from dataclasses import dataclass
from typing import List, Dict, Any
from nvme_cli_interface import NVMeCliInterface
from result_analyzer import ResultAnalyzer


@dataclass
class TestResult:
    """Test execution result container"""
    overall_status: str  # 'PASS' or 'FAIL'
    commands_executed: int
    commands_passed: int
    commands_failed: int
    execution_time: float
    failure_reasons: List[str]
    detailed_results: Dict[str, Any]
    raw_outputs: Dict[str, str]


class NVMeTestExecutor:
    """Main test executor for NVMe information command validation"""
    
    def __init__(self, config: Dict[str, Any], logger):
        self.config = config
        self.logger = logger
        self.nvme_interface = NVMeCliInterface(config, logger)
        self.result_analyzer = ResultAnalyzer(config, logger)
        
        # Test sequence - exact 8 commands from specification
        self.test_sequence = [
            ('nvme_list', 'List all NVMe devices'),
            ('nvme_id_ctrl', 'Get controller identification'),
            ('nvme_id_ns', 'Get namespace identification'),
            ('nvme_ns_descs', 'Get namespace descriptors'),
            ('nvme_show_regs', 'Display controller registers'),
            ('nvme_fw_log', 'Get firmware log information'),
            ('nvme_smart_log', 'Get SMART/health information'),
            ('nvme_error_log', 'Get error log entries')
        ]
    
    def validate_preconditions(self) -> bool:
        """Validate test pre-conditions"""
        
        self.logger.info("Validating test pre-conditions...")
        
        # Check if target device exists
        device_path = self.config['device']
        if not self.nvme_interface.validate_device_exists(device_path):
            self.logger.error(f"Target device {device_path} not found")
            return False
        
        # Validate namespace initialization (nsid = 1)
        if not self.nvme_interface.validate_namespace_initialized(device_path, nsid=1):
            self.logger.error("Namespace 1 is not properly initialized")
            return False
        
        # Check device accessibility
        if not self.nvme_interface.check_device_accessibility(device_path):
            self.logger.error("Device is not accessible for testing")
            return False
        
        self.logger.info("Pre-conditions validated successfully")
        return True
    
    def execute_test_sequence(self) -> TestResult:
        """Execute the complete 8-command test sequence"""
        
        start_time = time.time()
        command_results = {}
        raw_outputs = {}
        
        self.logger.info("Starting NVMe information command test sequence")
        
        # Validate pre-conditions
        if not self.validate_preconditions():
            return TestResult(
                overall_status='FAIL',
                commands_executed=0,
                commands_passed=0,
                commands_failed=0,
                execution_time=time.time() - start_time,
                failure_reasons=['Pre-condition validation failed'],
                detailed_results={},
                raw_outputs={}
            )
        
        # Execute each command in sequence
        for i, (command_name, description) in enumerate(self.test_sequence, 1):
            self.logger.info(f"[{i}/8] Executing {command_name}: {description}")
            
            try:
                # Execute command with timeout
                cmd_result = getattr(self.nvme_interface, command_name)()
                command_results[command_name] = cmd_result
                raw_outputs[command_name] = cmd_result.raw_output
                
                # Log command status
                if cmd_result.success:
                    self.logger.info(f"[{i}/8] {command_name} completed successfully")
                else:
                    self.logger.error(f"[{i}/8] {command_name} failed: {cmd_result.error_message}")
                
                # Add delay between commands for stability
                if i < len(self.test_sequence):
                    time.sleep(0.5)
                    
            except Exception as e:
                self.logger.error(f"[{i}/8] {command_name} exception: {str(e)}")
                command_results[command_name] = self._create_failed_result(command_name, str(e))
                raw_outputs[command_name] = f"Exception: {str(e)}"
        
        execution_time = time.time() - start_time
        
        # Analyze results using pass/fail criteria
        analysis_result = self.result_analyzer.analyze_test_results(command_results)
        
        # Count command statistics
        commands_executed = len(command_results)
        commands_passed = sum(1 for result in command_results.values() if result.success)
        commands_failed = commands_executed - commands_passed
        
        # Create final test result
        test_result = TestResult(
            overall_status=analysis_result.overall_status,
            commands_executed=commands_executed,
            commands_passed=commands_passed,
            commands_failed=commands_failed,
            execution_time=execution_time,
            failure_reasons=analysis_result.failure_reasons,
            detailed_results=analysis_result.detailed_analysis,
            raw_outputs=raw_outputs
        )
        
        self.logger.info(f"Test sequence completed in {execution_time:.2f} seconds")
        self.logger.info(f"Overall result: {test_result.overall_status}")
        
        return test_result
    
    def _create_failed_result(self, command_name: str, error_message: str):
        """Create a failed command result object"""
        from nvme_cli_interface import CommandResult
        return CommandResult(
            success=False,
            command=command_name,
            return_code=1,
            raw_output="",
            parsed_data={},
            error_message=error_message,
            execution_time=0.0
        )
    
    def execute_single_command(self, command_name: str) -> Dict[str, Any]:
        """Execute a single command for debugging purposes"""
        
        if command_name not in [cmd[0] for cmd in self.test_sequence]:
            raise ValueError(f"Invalid command name: {command_name}")
        
        self.logger.info(f"Executing single command: {command_name}")
        
        try:
            cmd_result = getattr(self.nvme_interface, command_name)()
            return {
                'success': cmd_result.success,
                'raw_output': cmd_result.raw_output,
                'parsed_data': cmd_result.parsed_data,
                'error_message': cmd_result.error_message,
                'execution_time': cmd_result.execution_time
            }
        except Exception as e:
            self.logger.error(f"Command {command_name} failed with exception: {str(e)}")
            return {
                'success': False,
                'raw_output': "",
                'parsed_data': {},
                'error_message': str(e),
                'execution_time': 0.0
            }
    
    def get_test_sequence_info(self) -> List[Dict[str, str]]:
        """Return information about the test sequence"""
        return [
            {
                'step': i,
                'command': cmd[0],
                'description': cmd[1]
            }
            for i, cmd in enumerate(self.test_sequence, 1)
        ]