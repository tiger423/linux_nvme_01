# Linux NVMe Information Command Test (linux_nvme_01)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![NVMe CLI](https://img.shields.io/badge/nvme--cli-required-green.svg)](https://github.com/linux-nvme/nvme-cli)

Enterprise-grade SSD reliability test program that validates NVMe device information functionality using nvme-cli tools. This test suite implements the `linux_nvme_information_cmd` specification for comprehensive NVMe device validation.

## Overview

This test program executes a standardized 8-command sequence to validate NVMe device information reporting capabilities. It's designed for enterprise SSD qualification and reliability testing with support for multiple device types and comprehensive pass/fail analysis.

### Key Features

- ✅ **Complete NVMe Information Validation** - 8-command test sequence per specification
- ✅ **Multi-Device Type Support** - Bravo, Delta, Echo, and Compete series devices
- ✅ **Enterprise-Grade Logging** - Comprehensive audit trails and TDS integration
- ✅ **Configurable Pass/Fail Criteria** - SMART, PCIe, command execution, and firmware health analysis
- ✅ **Production Ready** - Robust error handling and timeout management
- ✅ **Multiple Output Formats** - JSON, CSV, and raw command outputs

## Requirements

### System Requirements
- Linux operating system
- Python 3.6 or higher
- Root privileges (for NVMe device access)
- NVMe CLI tools installed

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/tiger423/linux_nvme_01.git
cd linux_nvme_01
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Verify NVMe CLI installation:**
```bash
nvme version
```

4. **Check device accessibility:**
```bash
sudo nvme list
```

## Quick Start

### Basic Usage
```bash
# Run test with default configuration
sudo python main.py

# Test specific device
sudo python main.py --device /dev/nvme1n1

# Test with device type specification
sudo python main.py --device /dev/nvme0n1 --device-type delta
```

### Advanced Usage
```bash
# Custom configuration file
sudo python main.py --config my_config.yaml

# Debug mode with detailed logging
sudo python main.py --runmode debug --log-level DEBUG

# Production mode with specific qualification ID
sudo python main.py --runmode prod --quid "my_qualification_2024"
```

## Command Line Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--config` | Configuration file path | `config.yaml` | `--config test.yaml` |
| `--device` | NVMe device path | `/dev/nvme0n1` | `--device /dev/nvme1n1` |
| `--device-type` | Device type | `bravo` | `--device-type delta` |
| `--runmode` | Execution mode | `prod` | `--runmode debug` |
| `--quid` | Qualification ID | None | `--quid "qual_2024"` |
| `--log-level` | Logging verbosity | `INFO` | `--log-level DEBUG` |
| `--output-dir` | Output directory | `./logs` | `--output-dir /tmp/test` |

## Device Types

The test suite supports four enterprise SSD device types with specific configurations:

### Bravo Series (Entry-Level Enterprise)
- **Interface**: PCIe Gen3 x4
- **Timeout**: 30 seconds
- **Namespaces**: 1
- **Use Case**: General enterprise workloads

### Delta Series (High-Performance)
- **Interface**: PCIe Gen4 x8
- **Timeout**: 25 seconds  
- **Namespaces**: 1
- **Use Case**: High-performance computing

### Echo Series (Multi-Tenant)
- **Interface**: PCIe Gen4 x4
- **Timeout**: 35 seconds
- **Namespaces**: 2
- **Use Case**: Multi-tenant environments

### Compete Series (Flagship)
- **Interface**: PCIe Gen4 x16
- **Timeout**: 20 seconds
- **Namespaces**: 4
- **Use Case**: Mission-critical applications

## Test Sequence

The test executes 8 standardized NVMe commands in sequence:

1. `nvme list` - List all NVMe devices
2. `nvme id-ctrl` - Get controller identification
3. `nvme id-ns` - Get namespace identification  
4. `nvme ns-descs` - Get namespace descriptors
5. `nvme show-regs` - Display controller registers
6. `nvme fw-log` - Get firmware log information
7. `nvme smart-log` - Get SMART/health information
8. `nvme error-log` - Get error log entries

### Pre-Conditions
- NVMe namespace must be initialized (nsid = 1)
- Device must be accessible and responsive
- Sufficient privileges for NVMe operations

## Pass/Fail Criteria

The test evaluates four critical criteria:

### 1. SMART Health Analysis (LID=0x02)
- **Pass**: No critical warnings (thermal warnings allowed)
- **Fail**: Media errors > 0, critical subsystem degradation

### 2. PCIe Link Status
- **Pass**: Link width and speed match device type expectations
- **Fail**: Degraded link performance below specifications

### 3. Command Execution
- **Pass**: All commands complete within timeout periods
- **Fail**: Command timeouts or response failures

### 4. Firmware Health
- **Pass**: Controller status normal (CSTS.CFS = 0)
- **Fail**: Controller fatal status detected (CSTS.CFS = 1)

## Configuration

### Basic Configuration (config.yaml)
```yaml
device: "/dev/nvme0n1"
device_type: "bravo"
runmode: "prod"
description: "NVMe Information Command Test"
quid: "nvme_info_qual_2024"

command_timeout: 30
log_level: "INFO"
output_dir: "./logs"

expected_pcie:
  width: 4
  speed: 3

smart_thresholds:
  max_temperature: 70
  min_available_spare: 10
  max_percent_used: 80
```

### Advanced Configuration Options
- **Timeout Management**: Per-device type timeout configurations
- **Threshold Customization**: SMART and performance thresholds
- **Output Control**: Multiple format support (JSON, CSV, raw)
- **TDS Integration**: Test Data System qualification support

## Output Files

The test generates multiple output files in the specified output directory:

### Log Files
- `nvme_test_YYYYMMDD_HHMMSS.log` - Detailed execution log
- `raw_outputs_YYYYMMDD_HHMMSS/` - Individual command outputs

### Result Files
- `nvme_test_results_YYYYMMDD_HHMMSS.json` - Comprehensive test results
- `nvme_test_summary_YYYYMMDD_HHMMSS.csv` - Summary for batch processing
- `tds_integration_YYYYMMDD_HHMMSS.json` - TDS system integration

## Example Output

### Successful Test Run
```
================================================================================
Linux NVMe Information Command Test (linux_nvme_01)
Enterprise SSD Reliability Test Program
================================================================================

Starting NVMe test on device: /dev/nvme0n1
Device type: bravo
Run mode: prod

[1/8] Executing nvme_list: List all NVMe devices
✓ nvme_list completed successfully (0.12s)

[2/8] Executing nvme_id_ctrl: Get controller identification
✓ nvme_id_ctrl completed successfully (0.08s)

[3/8] Executing nvme_id_ns: Get namespace identification
✓ nvme_id_ns completed successfully (0.06s)

[4/8] Executing nvme_ns_descs: Get namespace descriptors
✓ nvme_ns_descs completed successfully (0.05s)

[5/8] Executing nvme_show_regs: Display controller registers
✓ nvme_show_regs completed successfully (0.04s)

[6/8] Executing nvme_fw_log: Get firmware log information
✓ nvme_fw_log completed successfully (0.03s)

[7/8] Executing nvme_smart_log: Get SMART/health information
✓ nvme_smart_log completed successfully (0.02s)

[8/8] Executing nvme_error_log: Get error log entries
✓ nvme_error_log completed successfully (0.03s)

================================================================================
TEST EXECUTION SUMMARY
================================================================================
Overall Result: PASS
Commands Executed: 8
Commands Passed: 8
Commands Failed: 0

Log files written to: ./logs
Test duration: 2.45 seconds
```

### Failed Test Example
```
================================================================================
TEST EXECUTION SUMMARY
================================================================================
Overall Result: FAIL
Commands Executed: 8
Commands Passed: 7
Commands Failed: 1

Failure Reasons:
  - SMART_MEDIA_ERRORS_2
  - PCIE_LINK_WIDTH_MISMATCH_EXPECTED_x4_ACTUAL_x2
```

## Troubleshooting

### Common Issues

**Permission Denied**
```bash
# Solution: Run with sudo privileges
sudo python main.py
```

**Device Not Found**
```bash
# Check device path
sudo nvme list
# Update config.yaml with correct device path
```

**Command Timeouts**
```bash
# Increase timeout for device type
# Edit config.yaml:
command_timeout: 60
```

**NVMe CLI Not Found**
```bash
# Install nvme-cli
sudo apt-get install nvme-cli  # Ubuntu/Debian
sudo yum install nvme-cli      # RHEL/CentOS
```

### Debug Mode
For detailed troubleshooting, run in debug mode:
```bash
sudo python main.py --runmode debug --log-level DEBUG
```

### Log Analysis
Check detailed logs for specific failure analysis:
```bash
# View latest log file
tail -f logs/nvme_test_*.log

# Check raw command outputs
ls logs/raw_outputs_*/
```

## Enterprise Integration

### TDS (Test Data System) Integration
The test supports integration with Test Data Systems through:
- Qualification ID (quid) parameter
- Structured JSON output format
- Standardized result codes
- Audit trail preservation

### Batch Processing
CSV output format enables batch analysis:
```bash
# Combine multiple test results
cat logs/nvme_test_summary_*.csv > batch_results.csv
```

### Automated Testing
Integration with CI/CD pipelines:
```bash
# Return codes: 0=PASS, 1=FAIL
if sudo python main.py --device /dev/nvme0n1; then
    echo "Test PASSED"
else
    echo "Test FAILED"
fi
```

## Development

### Project Structure
```
linux_nvme_01/
├── main.py                    # Entry point and orchestration
├── nvme_test_executor.py      # Test execution engine
├── nvme_cli_interface.py      # NVMe CLI wrapper
├── result_analyzer.py         # Pass/fail analysis
├── config_parser.py           # Configuration management
├── test_logger.py             # Logging system
├── config.yaml                # Default configuration
├── requirements.txt           # Python dependencies
└── IMPLEMENTATION_DESIGN.md   # Technical documentation
```

### Adding New Device Types
1. Update `config_parser.py` with new device specifications
2. Add device-specific thresholds and timeouts
3. Update configuration documentation

### Extending Pass/Fail Criteria
1. Modify `result_analyzer.py` analysis functions
2. Add new validation methods
3. Update test result structures

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Commit changes: `git commit -am 'Add new feature'`
5. Push to branch: `git push origin feature/new-feature`
6. Submit a Pull Request

### Coding Standards
- Follow PEP 8 Python style guidelines
- Add comprehensive docstrings
- Include error handling and logging
- Maintain backward compatibility

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the implementation design document

## Changelog

### Version 1.0.0
- Initial release
- Complete 8-command test sequence implementation
- Multi-device type support (bravo/delta/echo/compete)
- Enterprise-grade logging and reporting
- TDS integration capability
- Comprehensive pass/fail criteria analysis

## Acknowledgments

- NVMe specification contributors
- Linux NVMe CLI development team
- Enterprise SSD testing community