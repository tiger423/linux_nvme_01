#!/usr/bin/env python3
"""
Linux NVMe Information Command Test (linux_nvme_01)
Enterprise SSD Reliability Test Program

Purpose: Validate firmware device information functionality using nvme-cli
Test: linux_nvme_information_cmd
"""

import sys
import argparse
import os
from pathlib import Path
from config_parser import ConfigParser
from nvme_test_executor import NVMeTestExecutor
from test_logger import TestLogger


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='NVMe Information Command Test - Enterprise SSD Reliability Testing'
    )
    
    parser.add_argument(
        '--config', 
        type=str, 
        default='config.yaml',
        help='Path to test configuration YAML file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--device',
        type=str,
        help='Target NVMe device path (e.g., /dev/nvme0n1) - overrides config'
    )
    
    parser.add_argument(
        '--device-type',
        choices=['bravo', 'delta', 'echo', 'compete'],
        help='Device type - overrides config'
    )
    
    parser.add_argument(
        '--runmode',
        choices=['prod', 'debug', 'dryrun'],
        default='prod',
        help='Test execution mode (default: prod)'
    )
    
    parser.add_argument(
        '--quid',
        type=str,
        help='Qualification ID for TDS integration - overrides config'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./logs',
        help='Output directory for logs and results (default: ./logs)'
    )
    
    return parser.parse_args()


def validate_environment():
    """Validate test environment prerequisites"""
    
    # Check if running as root or with sufficient privileges
    if os.geteuid() != 0:
        print("WARNING: Not running as root. Some NVMe commands may fail due to permissions.")
    
    # Check nvme-cli availability
    if os.system('which nvme > /dev/null 2>&1') != 0:
        print("ERROR: nvme-cli not found. Please install nvme-cli package.")
        return False
    
    return True


def main():
    """Main test execution entry point"""
    
    print("=" * 80)
    print("Linux NVMe Information Command Test (linux_nvme_01)")
    print("Enterprise SSD Reliability Test Program")
    print("=" * 80)
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    try:
        # Create output directory
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize configuration parser
        config_parser = ConfigParser(args.config)
        config = config_parser.load_config()
        
        # Override config with command line arguments
        if args.device:
            config['device'] = args.device
        if args.device_type:
            config['device_type'] = args.device_type
        if args.quid:
            config['quid'] = args.quid
        
        config['runmode'] = args.runmode
        config['log_level'] = args.log_level
        config['output_dir'] = args.output_dir
        
        # Initialize logger
        logger = TestLogger(config)
        logger.log_test_start(config)
        
        # Initialize test executor
        executor = NVMeTestExecutor(config, logger)
        
        # Execute test sequence
        print(f"\nStarting NVMe test on device: {config['device']}")
        print(f"Device type: {config['device_type']}")
        print(f"Run mode: {config['runmode']}")
        
        test_result = executor.execute_test_sequence()
        
        # Log final results
        logger.log_test_completion(test_result)
        
        # Print summary
        print("\n" + "=" * 80)
        print("TEST EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Overall Result: {'PASS' if test_result.overall_status == 'PASS' else 'FAIL'}")
        print(f"Commands Executed: {test_result.commands_executed}")
        print(f"Commands Passed: {test_result.commands_passed}")
        print(f"Commands Failed: {test_result.commands_failed}")
        
        if test_result.failure_reasons:
            print(f"\nFailure Reasons:")
            for reason in test_result.failure_reasons:
                print(f"  - {reason}")
        
        print(f"\nLog files written to: {args.output_dir}")
        print(f"Test duration: {test_result.execution_time:.2f} seconds")
        
        # Exit with appropriate code
        exit_code = 0 if test_result.overall_status == 'PASS' else 1
        sys.exit(exit_code)
        
    except FileNotFoundError as e:
        print(f"ERROR: Configuration file not found: {e}")
        sys.exit(1)
    except PermissionError as e:
        print(f"ERROR: Permission denied: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()