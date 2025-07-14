#!/usr/bin/env python3
"""
Test Runner for Banking AI Agent
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def run_tests():
    """Run all tests and generate report"""
    print("🏦 Banking AI Agent - Test Suite")
    print("=" * 50)
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Add src to Python path
    sys.path.insert(0, str(project_root / 'src'))
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'Unit Tests',
            'command': ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short'],
            'description': 'Core functionality tests'
        },
        {
            'name': 'Banking Scenarios',
            'command': ['python', '-m', 'pytest', 'tests/test_banking_scenarios.py', '-v'],
            'description': 'Banking-specific scenario tests'
        },
        {
            'name': 'Performance Tests',
            'command': ['python', '-m', 'pytest', 'tests/test_banking_scenarios.py::TestPerformanceMetrics', '-v'],
            'description': 'Performance and load tests'
        },
        {
            'name': 'Error Handling Tests',
            'command': ['python', '-m', 'pytest', 'tests/test_banking_scenarios.py::TestErrorHandling', '-v'],
            'description': 'Error handling and edge cases'
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n🧪 Running {scenario['name']}")
        print(f"📝 {scenario['description']}")
        print("-" * 30)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                scenario['command'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result.returncode == 0:
                status = "✅ PASSED"
                print(f"{status} ({duration:.2f}s)")
            else:
                status = "❌ FAILED"
                print(f"{status} ({duration:.2f}s)")
                print("Error output:")
                print(result.stderr)
            
            results.append({
                'name': scenario['name'],
                'status': status,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr
            })
            
        except subprocess.TimeoutExpired:
            status = "⏰ TIMEOUT"
            print(f"{status} (>300s)")
            results.append({
                'name': scenario['name'],
                'status': status,
                'duration': 300,
                'stdout': '',
                'stderr': 'Test timed out after 5 minutes'
            })
        
        except Exception as e:
            status = "💥 ERROR"
            print(f"{status} - {str(e)}")
            results.append({
                'name': scenario['name'],
                'status': status,
                'duration': 0,
                'stdout': '',
                'stderr': str(e)
            })
    
    # Generate summary report
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY REPORT")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = len([r for r in results if "PASSED" in r['status']])
    failed_tests = len([r for r in results if "FAILED" in r['status']])
    error_tests = len([r for r in results if "ERROR" in r['status'] or "TIMEOUT" in r['status']])
    
    print(f"Total Test Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Errors/Timeouts: {error_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for result in results:
        print(f"  {result['status']} {result['name']} ({result['duration']:.2f}s)")
    
    # Save detailed report
    report_file = project_root / 'test_report.txt'
    with open(report_file, 'w') as f:
        f.write("Banking AI Agent - Test Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Summary:\n")
        f.write(f"Total Test Suites: {total_tests}\n")
        f.write(f"Passed: {passed_tests}\n")
        f.write(f"Failed: {failed_tests}\n")
        f.write(f"Errors/Timeouts: {error_tests}\n")
        f.write(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n\n")
        
        for result in results:
            f.write(f"\n{result['name']} - {result['status']}\n")
            f.write("-" * 30 + "\n")
            f.write(f"Duration: {result['duration']:.2f}s\n")
            if result['stdout']:
                f.write("STDOUT:\n")
                f.write(result['stdout'])
                f.write("\n")
            if result['stderr']:
                f.write("STDERR:\n")
                f.write(result['stderr'])
                f.write("\n")
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return overall success
    return failed_tests == 0 and error_tests == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

