"""
Result Analyzer - Pass/Fail Criteria Implementation
Implements the 4 critical pass/fail criteria from linux_nvme_01 specification:
1. SMART(LID=0x02) analysis - Critical Warning & Media Error
2. PCIe Link Status - Link Width & Speed validation  
3. NVMe Command - Timeout & Response failure detection
4. Firmware Assert/Hang - CSTS.CFS=1 Fatal Error detection
"""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class AnalysisResult:
    """Container for overall analysis results"""
    overall_status: str  # 'PASS' or 'FAIL'
    failure_reasons: List[str]
    detailed_analysis: Dict[str, Any]


class ResultAnalyzer:
    """Analyzes test results against pass/fail criteria"""
    
    def __init__(self, config: Dict[str, Any], logger):
        self.config = config
        self.logger = logger
        self.device_type = config.get('device_type', 'bravo')
        
        # Device-specific expected parameters
        self.device_expectations = {
            'bravo': {
                'pcie_width': 4,     # x4
                'pcie_speed': 3,     # Gen3 (8.0 GT/s)
                'max_temp': 70
            },
            'delta': {
                'pcie_width': 8,     # x8  
                'pcie_speed': 4,     # Gen4 (16.0 GT/s)
                'max_temp': 75
            },
            'echo': {
                'pcie_width': 4,     # x4
                'pcie_speed': 4,     # Gen4 (16.0 GT/s) 
                'max_temp': 80
            },
            'compete': {
                'pcie_width': 16,    # x16
                'pcie_speed': 4,     # Gen4 (16.0 GT/s)
                'max_temp': 85
            }
        }
    
    def analyze_test_results(self, command_results: Dict[str, Any]) -> AnalysisResult:
        """Main analysis function - evaluates all pass/fail criteria"""
        
        self.logger.info("Starting pass/fail criteria analysis...")
        
        failure_reasons = []
        detailed_analysis = {}
        
        # Criterion 1: SMART(LID=0x02) Analysis
        smart_analysis = self._analyze_smart_data(command_results.get('nvme_smart_log'))
        detailed_analysis['smart_analysis'] = smart_analysis
        if smart_analysis['failed']:
            failure_reasons.extend(smart_analysis['failure_reasons'])
        
        # Criterion 2: PCIe Link Status Validation
        pcie_analysis = self._analyze_pcie_status(command_results.get('nvme_show_regs'))
        detailed_analysis['pcie_analysis'] = pcie_analysis
        if pcie_analysis['failed']:
            failure_reasons.extend(pcie_analysis['failure_reasons'])
        
        # Criterion 3: Command Execution Validation
        command_analysis = self._analyze_command_execution(command_results)
        detailed_analysis['command_analysis'] = command_analysis
        if command_analysis['failed']:
            failure_reasons.extend(command_analysis['failure_reasons'])
        
        # Criterion 4: Firmware Health Analysis
        firmware_analysis = self._analyze_firmware_health(command_results.get('nvme_show_regs'))
        detailed_analysis['firmware_analysis'] = firmware_analysis
        if firmware_analysis['failed']:
            failure_reasons.extend(firmware_analysis['failure_reasons'])
        
        # Determine overall status
        overall_status = 'PASS' if not failure_reasons else 'FAIL'
        
        self.logger.info(f"Analysis complete: {overall_status}")
        if failure_reasons:
            for reason in failure_reasons:
                self.logger.warning(f"Failure reason: {reason}")
        
        return AnalysisResult(
            overall_status=overall_status,
            failure_reasons=failure_reasons,
            detailed_analysis=detailed_analysis
        )
    
    def _analyze_smart_data(self, smart_command_result) -> Dict[str, Any]:
        """
        Analyze SMART data for critical warnings and media errors
        FAIL CONDITIONS:
        - Critical Warning (expect Thermal)
        - Media Error > 0
        """
        
        analysis = {
            'failed': False,
            'failure_reasons': [],
            'critical_warnings': {},
            'media_error_count': 0,
            'thermal_warning_allowed': True
        }
        
        if not smart_command_result or not smart_command_result.success:
            analysis['failed'] = True
            analysis['failure_reasons'].append('SMART_DATA_UNAVAILABLE')
            return analysis
        
        smart_data = smart_command_result.parsed_data
        
        # Analyze Critical Warning byte (LID=0x02)
        critical_warning = smart_data.get('critical_warning', 0)
        
        if critical_warning > 0:
            # Parse bit field (8 bits)
            warnings = {
                'available_spare_low': bool(critical_warning & 0x01),      # Bit 0
                'temperature_threshold': bool(critical_warning & 0x02),    # Bit 1 - THERMAL (ALLOWED)
                'nvm_subsystem_degraded': bool(critical_warning & 0x04),   # Bit 2 - CRITICAL
                'media_read_only': bool(critical_warning & 0x08),          # Bit 3 - CRITICAL  
                'volatile_backup_failed': bool(critical_warning & 0x10),   # Bit 4 - CRITICAL
                'reserved_bit_5': bool(critical_warning & 0x20),           # Bit 5
                'reserved_bit_6': bool(critical_warning & 0x40),           # Bit 6
                'reserved_bit_7': bool(critical_warning & 0x80)            # Bit 7
            }
            
            analysis['critical_warnings'] = warnings
            
            # Check for CRITICAL warnings (excluding thermal)
            critical_failures = []
            
            if warnings['available_spare_low']:
                critical_failures.append('SMART_AVAILABLE_SPARE_LOW')
            
            if warnings['nvm_subsystem_degraded']:
                critical_failures.append('SMART_NVM_SUBSYSTEM_DEGRADED')
            
            if warnings['media_read_only']:
                critical_failures.append('SMART_MEDIA_READ_ONLY')
            
            if warnings['volatile_backup_failed']:
                critical_failures.append('SMART_VOLATILE_BACKUP_FAILED')
            
            # Add critical failures to analysis
            if critical_failures:
                analysis['failed'] = True
                analysis['failure_reasons'].extend(critical_failures)
            
            # Log thermal warning but don't fail
            if warnings['temperature_threshold']:
                self.logger.warning("SMART thermal warning detected (allowed)")
        
        # Check Media Error count
        media_errors = smart_data.get('media_errors', 0)
        analysis['media_error_count'] = media_errors
        
        if media_errors > 0:
            analysis['failed'] = True
            analysis['failure_reasons'].append(f'SMART_MEDIA_ERRORS_{media_errors}')
        
        # Additional SMART health checks
        percent_used = smart_data.get('percent_used', 0)
        if percent_used >= 90:
            analysis['failure_reasons'].append('SMART_HIGH_WEAR_LEVEL')
            analysis['failed'] = True
        
        available_spare = smart_data.get('avail_spare', 100)
        spare_threshold = smart_data.get('spare_thresh', 10)
        if available_spare < spare_threshold:
            analysis['failure_reasons'].append('SMART_SPARE_BELOW_THRESHOLD')
            analysis['failed'] = True
        
        return analysis
    
    def _analyze_pcie_status(self, register_command_result) -> Dict[str, Any]:
        """
        Analyze PCIe Link Status for Link Width & Speed
        Validates against device type expectations
        """
        
        analysis = {
            'failed': False,
            'failure_reasons': [],
            'expected_width': None,
            'actual_width': None,
            'expected_speed': None,
            'actual_speed': None
        }
        
        if not register_command_result or not register_command_result.success:
            analysis['failed'] = True
            analysis['failure_reasons'].append('PCIE_REGISTER_DATA_UNAVAILABLE')
            return analysis
        
        register_data = register_command_result.parsed_data
        expected = self.device_expectations.get(self.device_type, self.device_expectations['bravo'])
        
        analysis['expected_width'] = expected['pcie_width']
        analysis['expected_speed'] = expected['pcie_speed']
        
        # Parse PCIe Link Status Register (LNKSTA)
        lnksta = register_data.get('lnksta')
        
        if lnksta is not None:
            # Extract link width from bits [9:4]
            actual_width = (lnksta >> 4) & 0x3F
            
            # Extract link speed from bits [3:0] 
            actual_speed = lnksta & 0x0F
            
            analysis['actual_width'] = actual_width
            analysis['actual_speed'] = actual_speed
            
            # Validate link width
            if actual_width != expected['pcie_width']:
                analysis['failed'] = True
                analysis['failure_reasons'].append(
                    f'PCIE_LINK_WIDTH_MISMATCH_EXPECTED_x{expected["pcie_width"]}_ACTUAL_x{actual_width}'
                )
            
            # Validate link speed
            if actual_speed < expected['pcie_speed']:  # Allow equal or higher speed
                speed_names = {1: 'Gen1', 2: 'Gen2', 3: 'Gen3', 4: 'Gen4', 5: 'Gen5'}
                expected_name = speed_names.get(expected['pcie_speed'], f'Gen{expected["pcie_speed"]}')
                actual_name = speed_names.get(actual_speed, f'Gen{actual_speed}')
                
                analysis['failed'] = True
                analysis['failure_reasons'].append(
                    f'PCIE_LINK_SPEED_BELOW_EXPECTED_{expected_name}_ACTUAL_{actual_name}'
                )
        else:
            # Try alternative register parsing if LNKSTA not found
            self.logger.warning("PCIe LNKSTA register not found, attempting alternative parsing")
            analysis['failed'] = True
            analysis['failure_reasons'].append('PCIE_LNKSTA_REGISTER_NOT_FOUND')
        
        return analysis
    
    def _analyze_command_execution(self, command_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze command execution for timeouts and response failures
        FAIL CONDITIONS:
        - Command timeout
        - Response failure (non-zero return code)
        """
        
        analysis = {
            'failed': False,
            'failure_reasons': [],
            'command_statistics': {
                'total_commands': 0,
                'successful_commands': 0,
                'failed_commands': 0,
                'timeout_commands': 0
            },
            'failed_command_details': []
        }
        
        for command_name, result in command_results.items():
            analysis['command_statistics']['total_commands'] += 1
            
            if result.success:
                analysis['command_statistics']['successful_commands'] += 1
            else:
                analysis['command_statistics']['failed_commands'] += 1
                
                # Categorize failure type
                if 'timeout' in result.error_message.lower():
                    analysis['command_statistics']['timeout_commands'] += 1
                    analysis['failure_reasons'].append(f'COMMAND_TIMEOUT_{command_name.upper()}')
                else:
                    analysis['failure_reasons'].append(f'COMMAND_RESPONSE_FAIL_{command_name.upper()}')
                
                analysis['failed_command_details'].append({
                    'command': command_name,
                    'error_message': result.error_message,
                    'return_code': result.return_code,
                    'execution_time': result.execution_time
                })
        
        # Mark as failed if any commands failed
        if analysis['command_statistics']['failed_commands'] > 0:
            analysis['failed'] = True
        
        return analysis
    
    def _analyze_firmware_health(self, register_command_result) -> Dict[str, Any]:
        """
        Analyze firmware health for fatal errors
        FAIL CONDITIONS:
        - Controller Fatal Status (CSTS.CFS = 1)
        - Controller not ready when expected
        """
        
        analysis = {
            'failed': False,
            'failure_reasons': [],
            'csts_register': None,
            'controller_ready': None,
            'fatal_error': None
        }
        
        if not register_command_result or not register_command_result.success:
            analysis['failed'] = True
            analysis['failure_reasons'].append('FIRMWARE_HEALTH_DATA_UNAVAILABLE')
            return analysis
        
        register_data = register_command_result.parsed_data
        
        # Analyze Controller Status Register (CSTS)
        csts = register_data.get('csts')
        
        if csts is not None:
            analysis['csts_register'] = csts
            
            # Check Controller Fatal Status bit (CFS) - bit 1
            fatal_error = bool(csts & 0x02)
            analysis['fatal_error'] = fatal_error
            
            if fatal_error:
                analysis['failed'] = True
                analysis['failure_reasons'].append('FIRMWARE_FATAL_ERROR_CSTS_CFS')
            
            # Check Controller Ready bit (RDY) - bit 0  
            controller_ready = bool(csts & 0x01)
            analysis['controller_ready'] = controller_ready
            
            if not controller_ready:
                analysis['failed'] = True
                analysis['failure_reasons'].append('FIRMWARE_CONTROLLER_NOT_READY')
            
            # Additional controller configuration checks
            cc = register_data.get('cc')
            if cc is not None:
                # Check if controller is enabled (EN bit - bit 0)
                controller_enabled = bool(cc & 0x01)
                if not controller_enabled:
                    self.logger.warning("Controller not enabled (CC.EN=0)")
        else:
            analysis['failed'] = True
            analysis['failure_reasons'].append('FIRMWARE_CSTS_REGISTER_NOT_FOUND')
        
        return analysis
    
    def get_device_type_expectations(self) -> Dict[str, Any]:
        """Return expected parameters for current device type"""
        return self.device_expectations.get(self.device_type, self.device_expectations['bravo'])
    
    def validate_test_completeness(self, command_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that all required commands were executed"""
        
        required_commands = [
            'nvme_list', 'nvme_id_ctrl', 'nvme_id_ns', 'nvme_ns_descs',
            'nvme_show_regs', 'nvme_fw_log', 'nvme_smart_log', 'nvme_error_log'
        ]
        
        missing_commands = []
        for cmd in required_commands:
            if cmd not in command_results:
                missing_commands.append(cmd)
        
        return {
            'complete': len(missing_commands) == 0,
            'missing_commands': missing_commands,
            'executed_commands': list(command_results.keys())
        }