"""
NVMe CLI Interface - Wrapper for NVMe Command Line Operations
Implements the 8 command sequence with proper error handling and parsing
"""

import subprocess
import time
import re
import os
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import json


@dataclass
class CommandResult:
    """Container for command execution results"""
    success: bool
    command: str
    return_code: int
    raw_output: str
    parsed_data: Dict[str, Any]
    error_message: str
    execution_time: float


class NVMeCliInterface:
    """Interface wrapper for NVMe CLI commands"""
    
    def __init__(self, config: Dict[str, Any], logger):
        self.config = config
        self.logger = logger
        self.device_path = config['device']
        self.command_timeout = config.get('command_timeout', 30)
        
    def _execute_command(self, cmd: List[str], description: str) -> CommandResult:
        """Execute a command with timeout and error handling"""
        
        start_time = time.time()
        cmd_str = ' '.join(cmd)
        
        self.logger.debug(f"Executing: {cmd_str}")
        
        try:
            result = subprocess.run(
                cmd,
                timeout=self.command_timeout,
                capture_output=True,
                text=True,
                check=False
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                self.logger.debug(f"Command successful: {description}")
                return CommandResult(
                    success=True,
                    command=cmd_str,
                    return_code=result.returncode,
                    raw_output=result.stdout,
                    parsed_data={},  # Will be populated by specific command handlers
                    error_message="",
                    execution_time=execution_time
                )
            else:
                error_msg = f"Command failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f": {result.stderr.strip()}"
                
                self.logger.warning(f"Command failed: {description} - {error_msg}")
                return CommandResult(
                    success=False,
                    command=cmd_str,
                    return_code=result.returncode,
                    raw_output=result.stdout,
                    parsed_data={},
                    error_message=error_msg,
                    execution_time=execution_time
                )
                
        except subprocess.TimeoutExpired:
            execution_time = self.command_timeout
            error_msg = f"Command timed out after {self.command_timeout} seconds"
            self.logger.error(f"Timeout: {description} - {error_msg}")
            
            return CommandResult(
                success=False,
                command=cmd_str,
                return_code=-1,
                raw_output="",
                parsed_data={},
                error_message=error_msg,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Exception during command execution: {str(e)}"
            self.logger.error(f"Exception: {description} - {error_msg}")
            
            return CommandResult(
                success=False,
                command=cmd_str,
                return_code=-2,
                raw_output="",
                parsed_data={},
                error_message=error_msg,
                execution_time=execution_time
            )
    
    def validate_device_exists(self, device_path: str) -> bool:
        """Validate that the target device exists"""
        return os.path.exists(device_path) and os.access(device_path, os.R_OK)
    
    def validate_namespace_initialized(self, device_path: str, nsid: int) -> bool:
        """Validate that namespace is properly initialized"""
        try:
            cmd = ['nvme', 'id-ns', device_path, '-n', str(nsid)]
            result = subprocess.run(cmd, timeout=10, capture_output=True, text=True, check=False)
            
            if result.returncode != 0:
                return False
            
            # Check for valid namespace size in output
            nsze_match = re.search(r'nsze\s*:\s*0x([0-9a-fA-F]+)', result.stdout)
            if nsze_match:
                nsze = int(nsze_match.group(1), 16)
                return nsze > 0
            
            return False
        except Exception:
            return False
    
    def check_device_accessibility(self, device_path: str) -> bool:
        """Check if device is accessible for testing"""
        try:
            # Try a simple list command to verify accessibility
            cmd = ['nvme', 'list']
            result = subprocess.run(cmd, timeout=10, capture_output=True, text=True, check=False)
            return result.returncode == 0 and device_path in result.stdout
        except Exception:
            return False
    
    # Command 1: nvme list
    def nvme_list(self) -> CommandResult:
        """Execute 'nvme list' command"""
        cmd = ['nvme', 'list']
        result = self._execute_command(cmd, "List all NVMe devices")
        
        if result.success:
            result.parsed_data = self._parse_nvme_list(result.raw_output)
        
        return result
    
    def _parse_nvme_list(self, output: str) -> Dict[str, Any]:
        """Parse nvme list output"""
        devices = []
        lines = output.strip().split('\n')
        
        # Find header line and data lines
        header_found = False
        for line in lines:
            if 'Node' in line and 'Model' in line:
                header_found = True
                continue
            
            if header_found and line.strip():
                # Parse device information from each line
                parts = line.split()
                if len(parts) >= 4:
                    devices.append({
                        'node': parts[0],
                        'sn': parts[1] if len(parts) > 1 else '',
                        'model': ' '.join(parts[2:-2]) if len(parts) > 3 else '',
                        'namespace': parts[-2] if len(parts) > 2 else '',
                        'size': parts[-1] if len(parts) > 1 else ''
                    })
        
        return {'devices': devices, 'target_found': any(self.device_path in d['node'] for d in devices)}
    
    # Command 2: nvme id-ctrl
    def nvme_id_ctrl(self) -> CommandResult:
        """Execute 'nvme id-ctrl' command"""
        cmd = ['nvme', 'id-ctrl', self.device_path]
        result = self._execute_command(cmd, "Get controller identification")
        
        if result.success:
            result.parsed_data = self._parse_controller_id(result.raw_output)
        
        return result
    
    def _parse_controller_id(self, output: str) -> Dict[str, Any]:
        """Parse controller identification data"""
        data = {}
        
        # Extract key controller information
        patterns = {
            'vid': r'vid\s*:\s*0x([0-9a-fA-F]+)',
            'ssvid': r'ssvid\s*:\s*0x([0-9a-fA-F]+)',
            'fr': r'fr\s*:\s*([A-Za-z0-9._-]+)',
            'mn': r'mn\s*:\s*([^\n]+)',
            'sn': r'sn\s*:\s*([A-Za-z0-9]+)',
            'mdts': r'mdts\s*:\s*(\d+)',
            'cntlid': r'cntlid\s*:\s*0x([0-9a-fA-F]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                if key in ['vid', 'ssvid', 'cntlid']:
                    data[key] = int(match.group(1), 16)
                elif key == 'mdts':
                    data[key] = int(match.group(1))
                else:
                    data[key] = match.group(1).strip()
        
        return data
    
    # Command 3: nvme id-ns
    def nvme_id_ns(self) -> CommandResult:
        """Execute 'nvme id-ns' command"""
        cmd = ['nvme', 'id-ns', self.device_path, '-n', '1']
        result = self._execute_command(cmd, "Get namespace identification")
        
        if result.success:
            result.parsed_data = self._parse_namespace_id(result.raw_output)
        
        return result
    
    def _parse_namespace_id(self, output: str) -> Dict[str, Any]:
        """Parse namespace identification data"""
        data = {}
        
        patterns = {
            'nsze': r'nsze\s*:\s*0x([0-9a-fA-F]+)',
            'ncap': r'ncap\s*:\s*0x([0-9a-fA-F]+)',
            'nuse': r'nuse\s*:\s*0x([0-9a-fA-F]+)',
            'lbaf': r'lbaf\s*(\d+)\s*:\s*ms:(\d+)\s+lbads:(\d+)',
            'nlbaf': r'nlbaf\s*:\s*(\d+)'
        }
        
        for key, pattern in patterns.items():
            if key == 'lbaf':
                # Handle LBA format specially
                matches = re.findall(pattern, output)
                if matches:
                    data['lba_formats'] = []
                    for match in matches:
                        data['lba_formats'].append({
                            'format_id': int(match[0]),
                            'metadata_size': int(match[1]),
                            'lba_data_size': int(match[2])
                        })
            else:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    if key in ['nsze', 'ncap', 'nuse']:
                        data[key] = int(match.group(1), 16)
                    else:
                        data[key] = int(match.group(1))
        
        return data
    
    # Command 4: nvme ns-descs
    def nvme_ns_descs(self) -> CommandResult:
        """Execute 'nvme ns-descs' command"""
        cmd = ['nvme', 'ns-descs', self.device_path, '-n', '1']
        result = self._execute_command(cmd, "Get namespace descriptors")
        
        if result.success:
            result.parsed_data = self._parse_namespace_descriptors(result.raw_output)
        
        return result
    
    def _parse_namespace_descriptors(self, output: str) -> Dict[str, Any]:
        """Parse namespace descriptors"""
        data = {}
        
        patterns = {
            'eui64': r'eui64\s*:\s*([0-9a-fA-F]+)',
            'nguid': r'nguid\s*:\s*([0-9a-fA-F]+)',
            'uuid': r'uuid\s*:\s*([0-9a-fA-F-]+)',
            'csi': r'csi\s*:\s*0x([0-9a-fA-F]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                data[key] = match.group(1)
        
        return data
    
    # Command 5: nvme show-regs
    def nvme_show_regs(self) -> CommandResult:
        """Execute 'nvme show-regs' command"""
        cmd = ['nvme', 'show-regs', self.device_path]
        result = self._execute_command(cmd, "Display controller registers")
        
        if result.success:
            result.parsed_data = self._parse_registers(result.raw_output)
        
        return result
    
    def _parse_registers(self, output: str) -> Dict[str, Any]:
        """Parse controller registers"""
        data = {}
        
        # Parse controller registers
        reg_patterns = {
            'cap': r'cap\s*:\s*0x([0-9a-fA-F]+)',
            'vs': r'vs\s*:\s*0x([0-9a-fA-F]+)',
            'cc': r'cc\s*:\s*0x([0-9a-fA-F]+)',
            'csts': r'csts\s*:\s*0x([0-9a-fA-F]+)',
            'aqa': r'aqa\s*:\s*0x([0-9a-fA-F]+)'
        }
        
        for reg, pattern in reg_patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                data[reg] = int(match.group(1), 16)
        
        # Parse PCIe configuration space if present
        pcie_patterns = {
            'lnksta': r'lnksta\s*:\s*0x([0-9a-fA-F]+)',
            'lnkcap': r'lnkcap\s*:\s*0x([0-9a-fA-F]+)'
        }
        
        for reg, pattern in pcie_patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                data[reg] = int(match.group(1), 16)
        
        return data
    
    # Command 6: nvme fw-log
    def nvme_fw_log(self) -> CommandResult:
        """Execute 'nvme fw-log' command"""
        cmd = ['nvme', 'fw-log', self.device_path]
        result = self._execute_command(cmd, "Get firmware log information")
        
        if result.success:
            result.parsed_data = self._parse_firmware_log(result.raw_output)
        
        return result
    
    def _parse_firmware_log(self, output: str) -> Dict[str, Any]:
        """Parse firmware log information"""
        data = {}
        
        # Parse firmware slots
        slot_pattern = r'frs(\d+)\s*\(([^)]*)\)\s*:\s*([A-Za-z0-9._-]+)'
        slots = re.findall(slot_pattern, output)
        
        data['firmware_slots'] = {}
        active_slot = None
        
        for slot_num, status, version in slots:
            data['firmware_slots'][f'slot_{slot_num}'] = {
                'version': version,
                'status': status.strip(),
                'active': 'Active' in status
            }
            
            if 'Active' in status:
                active_slot = slot_num
        
        data['active_slot'] = active_slot
        return data
    
    # Command 7: nvme smart-log
    def nvme_smart_log(self) -> CommandResult:
        """Execute 'nvme smart-log' command"""
        cmd = ['nvme', 'smart-log', self.device_path]
        result = self._execute_command(cmd, "Get SMART/health information")
        
        if result.success:
            result.parsed_data = self._parse_smart_log(result.raw_output)
        
        return result
    
    def _parse_smart_log(self, output: str) -> Dict[str, Any]:
        """Parse SMART log data"""
        data = {}
        
        patterns = {
            'critical_warning': r'critical_warning\s*:\s*0x([0-9a-fA-F]+)',
            'temperature': r'temperature\s*:\s*(\d+)',
            'avail_spare': r'avail_spare\s*:\s*(\d+)%',
            'spare_thresh': r'spare_thresh\s*:\s*(\d+)%',
            'percent_used': r'percent_used\s*:\s*(\d+)%',
            'media_errors': r'media_errors\s*:\s*(\d+)',
            'num_err_log_entries': r'num_err_log_entries\s*:\s*(\d+)',
            'power_cycles': r'power_cycles\s*:\s*(\d+)',
            'power_on_hours': r'power_on_hours\s*:\s*(\d+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                if key == 'critical_warning':
                    data[key] = int(match.group(1), 16)
                else:
                    data[key] = int(match.group(1))
        
        return data
    
    # Command 8: nvme error-log
    def nvme_error_log(self) -> CommandResult:
        """Execute 'nvme error-log' command"""
        cmd = ['nvme', 'error-log', self.device_path, '-e', '10']
        result = self._execute_command(cmd, "Get error log entries")
        
        if result.success:
            result.parsed_data = self._parse_error_log(result.raw_output)
        
        return result
    
    def _parse_error_log(self, output: str) -> Dict[str, Any]:
        """Parse error log entries"""
        data = {'error_entries': []}
        
        # Look for error entries in the output
        entry_pattern = r'Error Log Entry (\d+):\s*\n(.*?)(?=Error Log Entry|\Z)'
        entries = re.findall(entry_pattern, output, re.DOTALL)
        
        for entry_num, entry_content in entries:
            entry_data = {'entry_number': int(entry_num)}
            
            # Parse individual fields from entry content
            field_patterns = {
                'error_count': r'error_count\s*:\s*(\d+)',
                'sqid': r'sqid\s*:\s*(\d+)',
                'cmdid': r'cmdid\s*:\s*0x([0-9a-fA-F]+)',
                'status_field': r'status_field\s*:\s*0x([0-9a-fA-F]+)',
                'lba': r'lba\s*:\s*0x([0-9a-fA-F]+)',
                'nsid': r'nsid\s*:\s*(\d+)'
            }
            
            for field, pattern in field_patterns.items():
                match = re.search(pattern, entry_content, re.IGNORECASE)
                if match:
                    if field in ['cmdid', 'status_field', 'lba']:
                        entry_data[field] = int(match.group(1), 16)
                    else:
                        entry_data[field] = int(match.group(1))
            
            data['error_entries'].append(entry_data)
        
        data['total_entries'] = len(data['error_entries'])
        return data