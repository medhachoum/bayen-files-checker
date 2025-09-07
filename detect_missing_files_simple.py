#!/usr/bin/env python3
"""
Simplified Missing Files Detector for textData folder

Usage:
    python detect_missing_files_simple.py

This script will:
1. Scan textData folder for missing files
2. Print a summary to console
3. Generate a detailed JSON report
"""

import os
import json
from pathlib import Path
from datetime import datetime


def scan_for_missing_files(root_path="textData"):
    """
    Scan for missing files and return results.
    
    Returns:
        dict: Contains lists of empty folders and JSON-only folders
    """
    root = Path(root_path)
    results = {
        "empty_folders": [],
        "json_only_folders": [],
        "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if not root.exists():
        print(f"❌ Error: {root_path} folder not found!")
        return results
    
    print(f"🔍 Scanning {root_path} for missing files...")
    print("-" * 50)
    
    # Walk through all directories
    for current_dir, subdirs, files in os.walk(root):
        current_path = Path(current_dir)
        
        # Skip if it's not a leaf directory (has subdirectories)
        if subdirs:
            continue
            
        # Get relative path for reporting
        relative_path = current_path.relative_to(root)
        
        # Filter files by type
        md_files = [f for f in files if f.endswith('.md')]
        json_files = [f for f in files if f.endswith('.json')]
        other_files = [f for f in files if not f.endswith(('.json', '.md')) and not f.startswith('.')]
        
        # Check for missing files
        if not files or all(f.startswith('.') for f in files):
            # Completely empty folder
            results["empty_folders"].append(str(relative_path))
            print(f"❌ Empty: {relative_path}")
            
        elif json_files and not md_files and not other_files:
            # Only JSON files, missing main content
            results["json_only_folders"].append({
                "path": str(relative_path),
                "json_files": json_files
            })
            print(f"⚠️  JSON-only: {relative_path}")
            
        elif md_files:
            # Has proper content files
            print(f"✅ Valid: {relative_path}")
    
    return results


def main():
    """Main function"""
    # Scan for missing files
    results = scan_for_missing_files()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    print(f"Empty folders: {len(results['empty_folders'])}")
    print(f"JSON-only folders: {len(results['json_only_folders'])}")
    print(f"Total problematic folders: {len(results['empty_folders']) + len(results['json_only_folders'])}")
    
    # Save detailed report
    report_file = "missing_files_summary.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Show some examples if there are issues
    if results['empty_folders']:
        print(f"\n📁 First 5 empty folders:")
        for folder in results['empty_folders'][:5]:
            print(f"   • {folder}")
        if len(results['empty_folders']) > 5:
            print(f"   ... and {len(results['empty_folders']) - 5} more")
    
    if results['json_only_folders']:
        print(f"\n📋 JSON-only folders:")
        for item in results['json_only_folders']:
            print(f"   • {item['path']}")
            print(f"     JSON files: {', '.join(item['json_files'])}")


if __name__ == "__main__":
    main()