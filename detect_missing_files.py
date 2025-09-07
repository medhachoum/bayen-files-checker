#!/usr/bin/env python3
"""
Script to detect missing files in textData folder structure.

This script identifies folders that are either:
1. Completely empty
2. Contain only JSON files (missing main content files like .md)

Each leaf folder should contain main content files (like .md files) 
along with optional supporting files (.json, .log, etc.)
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime


class MissingFilesDetector:
    def __init__(self, root_path: str):
        """Initialize the detector with the root path to scan."""
        self.root_path = Path(root_path)
        self.missing_files_report = {
            "scan_date": datetime.now().isoformat(),
            "root_path": str(self.root_path),
            "empty_folders": [],
            "json_only_folders": [],
            "summary": {}
        }
    
    def is_leaf_folder(self, folder_path: Path) -> bool:
        """Check if a folder is a leaf folder (contains no subfolders)."""
        try:
            return not any(item.is_dir() for item in folder_path.iterdir())
        except PermissionError:
            print(f"Warning: Permission denied accessing {folder_path}")
            return False
    
    def get_file_types(self, folder_path: Path) -> Dict[str, List[str]]:
        """Get categorized file types in a folder."""
        file_types = {
            "json_files": [],
            "md_files": [],
            "log_files": [],
            "other_files": []
        }
        
        try:
            for item in folder_path.iterdir():
                if item.is_file():
                    file_name = item.name
                    if file_name.lower().endswith('.json'):
                        file_types["json_files"].append(file_name)
                    elif file_name.lower().endswith('.md'):
                        file_types["md_files"].append(file_name)
                    elif file_name.lower().endswith('.log'):
                        file_types["log_files"].append(file_name)
                    else:
                        file_types["other_files"].append(file_name)
        except PermissionError:
            print(f"Warning: Permission denied accessing files in {folder_path}")
        
        return file_types
    
    def scan_folder(self, folder_path: Path, relative_path: str = "") -> None:
        """Recursively scan folders to detect missing files."""
        try:
            # Skip system files and hidden directories
            if folder_path.name.startswith('.'):
                return
            
            # Update relative path
            current_relative = os.path.join(relative_path, folder_path.name) if relative_path else folder_path.name
            
            # Check if this is a leaf folder
            if self.is_leaf_folder(folder_path):
                self.check_leaf_folder(folder_path, current_relative)
            else:
                # Recursively scan subfolders
                for item in folder_path.iterdir():
                    if item.is_dir():
                        self.scan_folder(item, current_relative)
        
        except PermissionError:
            print(f"Warning: Permission denied accessing {folder_path}")
        except Exception as e:
            print(f"Error scanning {folder_path}: {e}")
    
    def check_leaf_folder(self, folder_path: Path, relative_path: str) -> None:
        """Check a leaf folder for missing files."""
        file_types = self.get_file_types(folder_path)
        
        # Count total files (excluding system files like .DS_Store)
        total_files = sum(len(files) for key, files in file_types.items() 
                         if key != "other_files" or not all(f.startswith('.') for f in files))
        
        # Filter out system files from other_files
        non_system_other_files = [f for f in file_types["other_files"] if not f.startswith('.')]
        actual_other_files = len(non_system_other_files)
        
        # Check if folder is empty
        if total_files == 0 and actual_other_files == 0:
            self.missing_files_report["empty_folders"].append({
                "path": relative_path,
                "absolute_path": str(folder_path),
                "issue": "Completely empty folder"
            })
            print(f"❌ Empty folder: {relative_path}")
        
        # Check if folder contains only JSON files (missing main content)
        elif (len(file_types["json_files"]) > 0 and 
              len(file_types["md_files"]) == 0 and 
              len(file_types["log_files"]) == 0 and 
              actual_other_files == 0):
            self.missing_files_report["json_only_folders"].append({
                "path": relative_path,
                "absolute_path": str(folder_path),
                "json_files": file_types["json_files"],
                "issue": "Contains only JSON files, missing main content files (.md)"
            })
            print(f"⚠️  JSON-only folder: {relative_path}")
            print(f"   JSON files: {', '.join(file_types['json_files'])}")
        
        # Report folders with proper content (for verification)
        elif len(file_types["md_files"]) > 0:
            print(f"✅ Valid folder: {relative_path} ({len(file_types['md_files'])} .md files)")
    
    def generate_report(self) -> None:
        """Generate summary statistics and save report."""
        # Generate summary
        self.missing_files_report["summary"] = {
            "total_empty_folders": len(self.missing_files_report["empty_folders"]),
            "total_json_only_folders": len(self.missing_files_report["json_only_folders"]),
            "total_problematic_folders": (
                len(self.missing_files_report["empty_folders"]) + 
                len(self.missing_files_report["json_only_folders"])
            )
        }
        
        # Save report to JSON file
        report_file = Path("missing_files_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.missing_files_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 SUMMARY:")
        print(f"Empty folders: {self.missing_files_report['summary']['total_empty_folders']}")
        print(f"JSON-only folders: {self.missing_files_report['summary']['total_json_only_folders']}")
        print(f"Total problematic folders: {self.missing_files_report['summary']['total_problematic_folders']}")
        print(f"\n📄 Detailed report saved to: {report_file.absolute()}")
    
    def run(self) -> None:
        """Run the missing files detection."""
        print(f"🔍 Scanning for missing files in: {self.root_path}")
        print("=" * 60)
        
        if not self.root_path.exists():
            print(f"❌ Error: Path does not exist: {self.root_path}")
            return
        
        if not self.root_path.is_dir():
            print(f"❌ Error: Path is not a directory: {self.root_path}")
            return
        
        # Start scanning
        self.scan_folder(self.root_path)
        
        # Generate and save report
        print("\n" + "=" * 60)
        self.generate_report()


def main():
    """Main function to run the missing files detector."""
    # Default path - can be modified as needed
    textdata_path = "textData"
    
    # Check if textData exists in current directory
    if not os.path.exists(textdata_path):
        print(f"❌ textData folder not found in current directory.")
        print(f"Current working directory: {os.getcwd()}")
        print("Please ensure you're running this script from the correct location.")
        return
    
    # Create detector and run
    detector = MissingFilesDetector(textdata_path)
    detector.run()


if __name__ == "__main__":
    main()