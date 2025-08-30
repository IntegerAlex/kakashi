#!/usr/bin/env python3
"""
Main Test Runner for Kakashi Performance Tests.

This script orchestrates all performance, stability, and compatibility tests
and provides comprehensive reporting for CI/CD pipelines.
"""

import sys
import os
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_command(cmd: List[str], description: str) -> Dict[str, Any]:
    """Run a command and return results."""
    print(f"\n🚀 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        end_time = time.time()
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": end_time - start_time,
            "description": description
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "Command timed out after 300 seconds",
            "duration": 300,
            "description": description
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "duration": 0,
            "description": description
        }

def install_dependencies() -> bool:
    """Install test dependencies."""
    print("📦 Installing test dependencies...")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not in a virtual environment")
    
    # Install requirements
    result = run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        "Installing test dependencies"
    )
    
    if not result["success"]:
        print(f"❌ Failed to install dependencies: {result['stderr']}")
        return False
    
    print("✅ Dependencies installed successfully")
    return True

def run_api_tests() -> Dict[str, Any]:
    """Run API compatibility tests."""
    print("\n🔧 Running API Compatibility Tests...")
    
    result = run_command(
        [sys.executable, "-m", "pytest", "test_api_compatibility.py", "-v", "--tb=short"],
        "API Compatibility Tests"
    )
    
    return result

def run_performance_tests() -> Dict[str, Any]:
    """Run performance benchmark tests."""
    print("\n⚡ Running Performance Benchmark Tests...")
    
    result = run_command(
        [sys.executable, "-m", "pytest", "test_performance.py", "-v", "--benchmark-only", "--benchmark-sort=mean"],
        "Performance Benchmark Tests"
    )
    
    return result

def run_stability_tests() -> Dict[str, Any]:
    """Run stability tests."""
    print("\n🛡️  Running Stability Tests...")
    
    result = run_command(
        [sys.executable, "-m", "pytest", "test_stability.py", "-v", "--tb=short"],
        "Stability Tests"
    )
    
    return result

def run_all_tests() -> Dict[str, Any]:
    """Run all tests with pytest."""
    print("\n🎯 Running All Tests...")
    
    result = run_command(
        [sys.executable, "-m", "pytest", "-v", "--tb=short", "--benchmark-only", "--benchmark-sort=mean"],
        "All Tests"
    )
    
    return result

def generate_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a comprehensive test report."""
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - successful_tests
    
    total_duration = sum(r["duration"] for r in results)
    
    report = {
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": total_duration
        },
        "results": results,
        "timestamp": time.time(),
        "python_version": sys.version,
        "platform": sys.platform
    }
    
    return report

def print_report(report: Dict[str, Any]):
    """Print a formatted test report."""
    summary = report["summary"]
    
    print("\n" + "="*80)
    print("📊 KAKASHI PERFORMANCE TEST REPORT")
    print("="*80)
    
    print(f"\n📈 Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Successful:  {summary['successful_tests']}")
    print(f"  Failed:      {summary['failed_tests']}")
    print(f"  Success Rate: {summary['success_rate']:.1f}%")
    print(f"  Total Duration: {summary['total_duration']:.2f}s")
    
    print(f"\n🐍 Environment:")
    print(f"  Python Version: {report['python_version']}")
    print(f"  Platform: {report['platform']}")
    
    print(f"\n📋 Detailed Results:")
    for result in report["results"]:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"  {status} {result['description']} ({result['duration']:.2f}s)")
        
        if not result["success"] and result["stderr"]:
            print(f"    Error: {result['stderr'][:200]}...")
    
    print("\n" + "="*80)
    
    # Overall result
    if summary["failed_tests"] == 0:
        print("🎉 ALL TESTS PASSED! Kakashi is performing excellently!")
    else:
        print(f"⚠️  {summary['failed_tests']} test(s) failed. Please review the results.")
    
    print("="*80)

def save_report(report: Dict[str, Any], filename: str = "test_report.json"):
    """Save the test report to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Test report saved to: {filename}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Kakashi Performance Test Runner")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies first")
    parser.add_argument("--api-only", action="store_true", help="Run only API compatibility tests")
    parser.add_argument("--performance-only", action="store_true", help="Run only performance tests")
    parser.add_argument("--stability-only", action="store_true", help="Run only stability tests")
    parser.add_argument("--save-report", action="store_true", help="Save detailed report to JSON")
    parser.add_argument("--report-file", default="test_report.json", help="Report filename")
    
    args = parser.parse_args()
    
    print("🚀 Kakashi Performance Test Suite")
    print("="*50)
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
    
    results = []
    
    try:
        # Run tests based on arguments
        if args.api_only:
            results.append(run_api_tests())
        elif args.performance_only:
            results.append(run_performance_tests())
        elif args.stability_only:
            results.append(run_stability_tests())
        else:
            # Run all tests
            results.append(run_api_tests())
            results.append(run_performance_tests())
            results.append(run_stability_tests())
        
        # Generate and display report
        report = generate_report(results)
        print_report(report)
        
        # Save report if requested
        if args.save_report:
            save_report(report, args.report_file)
        
        # Exit with appropriate code
        if report["summary"]["failed_tests"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
