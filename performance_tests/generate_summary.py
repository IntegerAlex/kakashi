#!/usr/bin/env python3
"""
Summary Report Generator for Kakashi Performance Tests.

This script aggregates results from all test runs and generates
comprehensive reports for CI/CD pipelines.
"""

import sys
import os
import json
import glob
from pathlib import Path
from typing import Dict, List, Any
import argparse
from datetime import datetime

def load_test_results(results_dir: str) -> Dict[str, Any]:
    """Load all test results from the results directory."""
    results = {}
    
    # Find all test result files
    xml_files = glob.glob(os.path.join(results_dir, "**/*.xml"), recursive=True)
    json_files = glob.glob(os.path.join(results_dir, "**/*.json"), recursive=True)
    
    print(f"Found {len(xml_files)} XML files and {len(json_files)} JSON files")
    
    # Load JSON reports
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            # Extract Python version from filename
            filename = os.path.basename(json_file)
            if 'test-report-' in filename:
                version = filename.replace('test-report-', '').replace('.json', '')
                results[f"python_{version}"] = data
                
        except Exception as e:
            print(f"Warning: Could not load {json_file}: {e}")
    
    return results

def analyze_performance_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze performance test results."""
    analysis = {
        "total_runs": len(results),
        "successful_runs": 0,
        "failed_runs": 0,
        "python_versions": [],
        "performance_metrics": {},
        "stability_metrics": {},
        "api_compatibility": {}
    }
    
    for version, data in results.items():
        analysis["python_versions"].append(version)
        
        if data.get("summary", {}).get("failed_tests", 0) == 0:
            analysis["successful_runs"] += 1
        else:
            analysis["failed_runs"] += 1
    
    return analysis

def generate_markdown_report(analysis: Dict[str, Any], results: Dict[str, Any]) -> str:
    """Generate a markdown report."""
    report = []
    
    # Header
    report.append("# 🚀 Kakashi Performance Test Summary Report")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("")
    
    # Executive Summary
    report.append("## 📊 Executive Summary")
    report.append("")
    
    total_runs = analysis["total_runs"]
    successful_runs = analysis["successful_runs"]
    failed_runs = analysis["failed_runs"]
    success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
    
    report.append(f"- **Total Test Runs:** {total_runs}")
    report.append(f"- **Successful Runs:** {successful_runs}")
    report.append(f"- **Failed Runs:** {failed_runs}")
    report.append(f"- **Success Rate:** {success_rate:.1f}%")
    report.append("")
    
    if failed_runs == 0:
        report.append("🎉 **All test runs passed successfully!**")
    else:
        report.append(f"⚠️ **{failed_runs} test run(s) failed.**")
    report.append("")
    
    # Python Version Compatibility
    report.append("## 🐍 Python Version Compatibility")
    report.append("")
    
    for version in analysis["python_versions"]:
        if version in results:
            data = results[version]
            summary = data.get("summary", {})
            
            status = "✅ PASS" if summary.get("failed_tests", 0) == 0 else "❌ FAIL"
            report.append(f"- **Python {version}:** {status}")
            
            if "failed_tests" in summary:
                report.append(f"  - Tests: {summary.get('total_tests', 0)}")
                report.append(f"  - Duration: {summary.get('total_duration', 0):.2f}s")
    
    report.append("")
    
    # Detailed Results
    report.append("## 📋 Detailed Results")
    report.append("")
    
    for version, data in results.items():
        report.append(f"### Python {version}")
        report.append("")
        
        summary = data.get("summary", {})
        report.append(f"- **Status:** {'✅ PASS' if summary.get('failed_tests', 0) == 0 else '❌ FAIL'}")
        report.append(f"- **Total Tests:** {summary.get('total_tests', 0)}")
        report.append(f"- **Successful:** {summary.get('successful_tests', 0)}")
        report.append(f"- **Failed:** {summary.get('failed_tests', 0)}")
        report.append(f"- **Duration:** {summary.get('total_duration', 0):.2f}s")
        report.append("")
        
        # Individual test results
        if "results" in data:
            report.append("#### Test Results:")
            for test_result in data["results"]:
                status = "✅ PASS" if test_result.get("success") else "❌ FAIL"
                report.append(f"- {status} {test_result.get('description', 'Unknown')} ({test_result.get('duration', 0):.2f}s)")
                
                if not test_result.get("success") and test_result.get("stderr"):
                    stderr = test_result["stderr"][:200]
                    if len(test_result["stderr"]) > 200:
                        stderr += "..."
                    report.append(f"  - Error: `{stderr}`")
            report.append("")
    
    # Recommendations
    report.append("## 💡 Recommendations")
    report.append("")
    
    if failed_runs == 0:
        report.append("- 🎉 **Excellent!** All tests are passing across all Python versions.")
        report.append("- 🚀 **Ready for Production:** Kakashi is performing excellently.")
        report.append("- 📈 **Consider:** Running extended stability tests for production validation.")
    else:
        report.append("- 🔍 **Investigate:** Failed test runs to identify root causes.")
        report.append("- 🧪 **Debug:** Check specific error messages and test environments.")
        report.append("- 📊 **Monitor:** Track performance metrics for regressions.")
    
    report.append("")
    
    # Footer
    report.append("---")
    report.append("*Report generated automatically by Kakashi CI/CD pipeline*")
    
    return "\n".join(report)

def generate_json_report(analysis: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a JSON report."""
    return {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "tool": "kakashi-performance-summary",
            "version": "1.0.0"
        },
        "analysis": analysis,
        "results": results
    }

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate Kakashi Performance Test Summary")
    parser.add_argument("results_dir", help="Directory containing test results")
    parser.add_argument("--output-dir", default=".", help="Output directory for reports")
    parser.add_argument("--format", choices=["both", "markdown", "json"], default="both", help="Output format")
    
    args = parser.parse_args()
    
    print("📊 Kakashi Performance Test Summary Generator")
    print("=" * 50)
    
    # Load test results
    print(f"📁 Loading test results from: {args.results_dir}")
    results = load_test_results(args.results_dir)
    
    if not results:
        print("❌ No test results found!")
        sys.exit(1)
    
    print(f"✅ Loaded {len(results)} test result sets")
    
    # Analyze results
    print("🔍 Analyzing test results...")
    analysis = analyze_performance_results(results)
    
    # Generate reports
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    if args.format in ["both", "markdown"]:
        print("📝 Generating markdown report...")
        markdown_report = generate_markdown_report(analysis, results)
        
        markdown_file = output_dir / "summary-report.md"
        with open(markdown_file, 'w') as f:
            f.write(markdown_report)
        
        print(f"✅ Markdown report saved to: {markdown_file}")
    
    if args.format in ["both", "json"]:
        print("📊 Generating JSON report...")
        json_report = generate_json_report(analysis, results)
        
        json_file = output_dir / "summary-report.json"
        with open(json_file, 'w') as f:
            json.dump(json_report, f, indent=2)
        
        print(f"✅ JSON report saved to: {json_file}")
    
    # Print summary
    print("\n📊 Summary:")
    print(f"  Total Runs: {analysis['total_runs']}")
    print(f"  Successful: {analysis['successful_runs']}")
    print(f"  Failed: {analysis['failed_runs']}")
    print(f"  Success Rate: {(analysis['successful_runs'] / analysis['total_runs'] * 100):.1f}%")
    
    if analysis['failed_runs'] == 0:
        print("\n🎉 All test runs passed successfully!")
        sys.exit(0)
    else:
        print(f"\n⚠️ {analysis['failed_runs']} test run(s) failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
