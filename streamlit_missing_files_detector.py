#!/usr/bin/env python3
"""
Streamlit Application for Missing Files Detection

This app provides a web interface to:
1. Select folders to scan
2. Visualize missing files in an interactive way
3. Generate detailed reports
4. Export results

Run with: streamlit run streamlit_missing_files_detector.py
"""

import streamlit as st
import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Tuple
import base64
import threading
import zipfile
import tempfile
import shutil

# Optional tkinter import for local environments
try:
    import tkinter as tk
    from tkinter import filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None
    filedialog = None


class StreamlitMissingFilesDetector:
    def __init__(self):
        """Initialize the Streamlit detector."""
        self.results = {
            "scan_date": None,
            "root_path": None,
            "empty_folders": [],
            "json_only_folders": [],
            "folders_with_empty_files": [],  # New category
            "valid_folders": [],
            "summary": {}
        }
    
    def select_folder_dialog(self) -> str:
        """Open a folder selection dialog and return the selected path."""
        if not TKINTER_AVAILABLE:
            st.error("🌐 Folder dialog is not available in cloud environment. Please enter the folder path manually.")
            st.info("💡 Tip: You can use paths like 'textData' or upload your data to the cloud environment first.")
            return ""
        
        try:
            # Create a root window and hide it
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1)
            
            # Set window icon if available
            try:
                root.iconbitmap(default='folder.ico')
            except:
                pass  # Icon file not found, continue without it
            
            # Open folder dialog
            folder_path = filedialog.askdirectory(
                title="Select Folder to Scan - Missing Files Detector",
                initialdir=os.getcwd(),
                mustexist=True
            )
            
            # Destroy the root window
            root.destroy()
            
            return folder_path if folder_path else ""
        
        except Exception as e:
            st.error(f"Error opening folder dialog: {e}")
            return ""
    
    def handle_folder_selection(self):
        """Handle folder selection with proper session state management."""
        selected_path = self.select_folder_dialog()
        if selected_path:
            return selected_path
        return None
    
    def get_available_folders(self, base_path: str = ".") -> List[str]:
        """Get list of available folders to scan."""
        folders = []
        try:
            for item in Path(base_path).iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    folders.append(str(item))
        except Exception as e:
            st.error(f"Error reading folders: {e}")
        return sorted(folders)
    
    def extract_zip_file(self, uploaded_file, progress_bar=None) -> Tuple[str, Dict]:
        """Extract ZIP file and return extraction directory and structure info."""
        try:
            # Create temporary directory for extraction
            temp_dir = tempfile.mkdtemp(prefix="zip_scan_")
            
            # Save uploaded file to temporary location
            zip_path = os.path.join(temp_dir, "uploaded.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Extract ZIP file
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            structure_info = {
                "total_files": 0,
                "total_folders": 0,
                "file_types": {},
                "folder_structure": []
            }
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get file list for progress tracking
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                # Extract files with progress
                for idx, file_name in enumerate(file_list):
                    if progress_bar:
                        progress_bar.progress((idx + 1) / total_files)
                    
                    # Extract individual file
                    zip_ref.extract(file_name, extract_dir)
                    
                    # Analyze structure
                    file_path = Path(file_name)
                    if file_name.endswith('/'):
                        structure_info["total_folders"] += 1
                        structure_info["folder_structure"].append(file_name)
                    else:
                        structure_info["total_files"] += 1
                        # Track file types
                        suffix = file_path.suffix.lower()
                        if suffix:
                            structure_info["file_types"][suffix] = structure_info["file_types"].get(suffix, 0) + 1
                        else:
                            structure_info["file_types"]["no_extension"] = structure_info["file_types"].get("no_extension", 0) + 1
            
            return extract_dir, structure_info
            
        except zipfile.BadZipFile:
            st.error("❌ Invalid ZIP file. Please upload a valid ZIP archive.")
            return None, None
        except Exception as e:
            st.error(f"❌ Error extracting ZIP file: {e}")
            return None, None
    
    def cleanup_temp_directory(self, temp_dir: str):
        """Clean up temporary extraction directory."""
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            st.warning(f"Could not clean up temporary directory: {e}")
    
    def display_zip_structure(self, structure_info: Dict):
        """Display ZIP file structure information."""
        if not structure_info:
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📁 Total Folders", structure_info["total_folders"])
            st.metric("📄 Total Files", structure_info["total_files"])
        
        with col2:
            if structure_info["file_types"]:
                st.write("**File Types:**")
                for ext, count in sorted(structure_info["file_types"].items()):
                    if ext == "no_extension":
                        st.write(f"• No extension: {count} files")
                    else:
                        st.write(f"• {ext}: {count} files")
        
        # Show folder structure preview (first 10 folders)
        if structure_info["folder_structure"]:
            with st.expander("📂 Folder Structure Preview", expanded=False):
                preview_folders = structure_info["folder_structure"][:10]
                for folder in preview_folders:
                    st.code(folder, language=None)
                
                if len(structure_info["folder_structure"]) > 10:
                    st.info(f"... and {len(structure_info['folder_structure']) - 10} more folders")
    
    def is_leaf_folder(self, folder_path: Path) -> bool:
        """Check if a folder is a leaf folder (contains no subfolders)."""
        try:
            return not any(item.is_dir() for item in folder_path.iterdir())
        except PermissionError:
            return False
    
    def get_file_types(self, folder_path: Path) -> Dict[str, List[str]]:
        """Get categorized file types in a folder."""
        file_types = {
            "json_files": [],
            "md_files": [],
            "log_files": [],
            "other_files": [],
            "empty_files": []  # New category for empty files
        }
        
        try:
            for item in folder_path.iterdir():
                if item.is_file():
                    file_name = item.name
                    
                    # Check if file is empty (0 bytes)
                    try:
                        file_size = item.stat().st_size
                        is_empty = file_size == 0
                    except:
                        is_empty = False
                    
                    # Categorize by file type
                    if file_name.lower().endswith('.json'):
                        if is_empty:
                            file_types["empty_files"].append(file_name)
                        else:
                            file_types["json_files"].append(file_name)
                    elif file_name.lower().endswith('.md'):
                        if is_empty:
                            file_types["empty_files"].append(file_name)
                        else:
                            file_types["md_files"].append(file_name)
                    elif file_name.lower().endswith('.log'):
                        if is_empty:
                            file_types["empty_files"].append(file_name)
                        else:
                            file_types["log_files"].append(file_name)
                    else:
                        # Filter out system files
                        if not file_name.startswith('.'):
                            if is_empty:
                                file_types["empty_files"].append(file_name)
                            else:
                                file_types["other_files"].append(file_name)
        except PermissionError:
            pass
        
        return file_types
    
    def scan_folder(self, folder_path: Path, progress_bar=None) -> None:
        """Recursively scan folders to detect missing files."""
        try:
            # Skip system files and hidden directories
            if folder_path.name.startswith('.'):
                return
            
            # Get all subdirectories for progress tracking
            all_dirs = []
            for root, dirs, files in os.walk(folder_path):
                # Filter out hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                all_dirs.extend([Path(root) / d for d in dirs])
            
            # Add leaf directories
            leaf_dirs = []
            for root, dirs, files in os.walk(folder_path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                if not dirs:  # This is a leaf directory
                    leaf_dirs.append(Path(root))
            
            total_dirs = len(leaf_dirs)
            
            # Check each leaf folder
            for idx, current_dir in enumerate(leaf_dirs):
                if progress_bar:
                    progress_bar.progress((idx + 1) / total_dirs)
                
                relative_path = current_dir.relative_to(folder_path)
                self.check_leaf_folder(current_dir, str(relative_path))
        
        except Exception as e:
            st.error(f"Error scanning {folder_path}: {e}")
    
    def check_leaf_folder(self, folder_path: Path, relative_path: str) -> None:
        """Check a leaf folder for missing files and empty files."""
        file_types = self.get_file_types(folder_path)
        
        # Count total files (excluding system files)
        total_files = sum(len(files) for key, files in file_types.items() if key != "empty_files")
        empty_files_count = len(file_types["empty_files"])
        
        folder_info = {
            "path": relative_path,
            "absolute_path": str(folder_path),
            "file_counts": {
                "md_files": len(file_types["md_files"]),
                "json_files": len(file_types["json_files"]),
                "log_files": len(file_types["log_files"]),
                "other_files": len(file_types["other_files"]),
                "empty_files": empty_files_count
            },
            "files": file_types
        }
        
        # Priority 1: Check if folder is completely empty
        if total_files == 0 and empty_files_count == 0:
            folder_info["issue"] = "Completely empty folder"
            folder_info["severity"] = "high"
            self.results["empty_folders"].append(folder_info)
        
        # Priority 2: Check if folder contains only JSON files (missing main content)
        elif (len(file_types["json_files"]) > 0 and 
              len(file_types["md_files"]) == 0 and 
              len(file_types["log_files"]) == 0 and 
              len(file_types["other_files"]) == 0 and
              empty_files_count == 0):
            folder_info["issue"] = "Contains only JSON files, missing main content files (.md)"
            folder_info["severity"] = "high"
            self.results["json_only_folders"].append(folder_info)
        
        # Priority 3: Check if folder has empty files (new criteria)
        elif empty_files_count > 0:
            if len(file_types["md_files"]) > 0:
                # Has content but also has empty files
                folder_info["issue"] = f"Folder has content but contains {empty_files_count} empty file(s)"
                folder_info["severity"] = "medium"
            else:
                # No main content and has empty files
                folder_info["issue"] = f"No main content files, contains {empty_files_count} empty file(s)"
                folder_info["severity"] = "high"
            
            self.results["folders_with_empty_files"].append(folder_info)
        
        # Valid folders with proper content
        elif len(file_types["md_files"]) > 0:
            folder_info["issue"] = "Valid folder with content"
            folder_info["severity"] = "none"
            self.results["valid_folders"].append(folder_info)
    
    def generate_summary(self) -> None:
        """Generate summary statistics."""
        self.results["summary"] = {
            "total_empty_folders": len(self.results["empty_folders"]),
            "total_json_only_folders": len(self.results["json_only_folders"]),
            "total_folders_with_empty_files": len(self.results["folders_with_empty_files"]),
            "total_valid_folders": len(self.results["valid_folders"]),
            "total_problematic_folders": (
                len(self.results["empty_folders"]) + 
                len(self.results["json_only_folders"]) +
                len(self.results["folders_with_empty_files"])
            ),
            "total_scanned_folders": (
                len(self.results["empty_folders"]) + 
                len(self.results["json_only_folders"]) + 
                len(self.results["folders_with_empty_files"]) +
                len(self.results["valid_folders"])
            )
        }
    
    def run_scan(self, selected_folder: str) -> Dict:
        """Run the missing files detection scan."""
        # Reset results
        self.results = {
            "scan_date": datetime.now().isoformat(),
            "root_path": selected_folder,
            "empty_folders": [],
            "json_only_folders": [],
            "folders_with_empty_files": [],
            "valid_folders": [],
            "summary": {}
        }
        
        folder_path = Path(selected_folder)
        
        if not folder_path.exists():
            st.error(f"Selected folder does not exist: {selected_folder}")
            return self.results
        
        if not folder_path.is_dir():
            st.error(f"Selected path is not a directory: {selected_folder}")
            return self.results
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text(f"Scanning folder: {selected_folder}")
        
        # Start scanning
        self.scan_folder(folder_path, progress_bar)
        
        # Generate summary
        self.generate_summary()
        
        progress_bar.progress(1.0)
        status_text.text("Scan completed!")
        
        return self.results


def create_download_link(data, filename, link_text):
    """Create a download link for data."""
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    b64 = base64.b64encode(json_str.encode('utf-8')).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="{filename}">{link_text}</a>'
    return href


def display_folder_details(folders_data, title, color, icon):
    """Display detailed information about folders."""
    if not folders_data:
        st.info(f"No {title.lower()} found.")
        return
    
    st.markdown(f"### {icon} {title} ({len(folders_data)} folders)")
    
    # Create expandable sections for each folder
    for idx, folder in enumerate(folders_data):
        folder_name = folder['path']
        
        # Create columns for better layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            with st.expander(f"📁 {folder_name}", expanded=False):
                st.markdown(f"**Path:** `{folder['absolute_path']}`")
                st.markdown(f"**Issue:** {folder['issue']}")
                
                # File counts
                counts = folder['file_counts']
                col_md, col_json, col_log, col_other, col_empty = st.columns(5)
                
                with col_md:
                    st.metric("MD Files", counts['md_files'])
                with col_json:
                    st.metric("JSON Files", counts['json_files'])
                with col_log:
                    st.metric("Log Files", counts['log_files'])
                with col_other:
                    st.metric("Other Files", counts['other_files'])
                with col_empty:
                    empty_count = counts.get('empty_files', 0)
                    if empty_count > 0:
                        st.metric("Empty Files", empty_count, delta_color="inverse")
                    else:
                        st.metric("Empty Files", empty_count)
                
                # List actual files if any exist
                files = folder['files']
                if any(files.values()):
                    st.markdown("**Files:**")
                    
                    for file_type, file_list in files.items():
                        if file_list:
                            file_type_name = file_type.replace('_', ' ').title()
                            st.markdown(f"- **{file_type_name}:** {', '.join(file_list)}")
        
        with col2:
            # Status indicator based on severity
            severity = folder.get('severity', 'none')
            issue = folder['issue']
            
            if severity == 'none' or "Valid folder" in issue:
                st.success("✅ Valid")
            elif severity == 'high' or "empty" in issue.lower() or "only JSON" in issue:
                st.error("❌ Critical")
            elif severity == 'medium' or "empty file" in issue.lower():
                st.warning("⚠️ Issues")
            else:
                st.info("🔍 Unknown")


def create_visualizations(results):
    """Create interactive visualizations for the results."""
    summary = results['summary']
    
    # Summary metrics
    st.markdown("### 📊 Summary Dashboard")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Scanned",
            summary['total_scanned_folders'],
            delta=None
        )
    
    with col2:
        st.metric(
            "Empty Folders",
            summary['total_empty_folders'],
            delta=None,
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "JSON-Only Folders",
            summary['total_json_only_folders'],
            delta=None,
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "Empty Files Issues",
            summary['total_folders_with_empty_files'],
            delta=None,
            delta_color="inverse"
        )
    
    with col5:
        st.metric(
            "Valid Folders",
            summary['total_valid_folders'],
            delta=None
        )
    
    # Charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Pie chart for folder status
        labels = ['Empty Folders', 'JSON-Only Folders', 'Empty Files Issues', 'Valid Folders']
        values = [
            summary['total_empty_folders'],
            summary['total_json_only_folders'],
            summary['total_folders_with_empty_files'],
            summary['total_valid_folders']
        ]
        colors = ['#FF6B6B', '#FFE66D', '#FF8C42', '#4ECDC4']
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            textinfo='label+percent+value'
        )])
        
        fig_pie.update_layout(
            title="Folder Status Distribution",
            font=dict(size=12)
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_chart2:
        # Bar chart for problems
        problem_types = ['Empty Folders', 'JSON-Only Folders', 'Empty Files Issues']
        problem_counts = [
            summary['total_empty_folders'],
            summary['total_json_only_folders'],
            summary['total_folders_with_empty_files']
        ]
        
        fig_bar = go.Figure([go.Bar(
            x=problem_types,
            y=problem_counts,
            marker_color=['#FF6B6B', '#FFE66D', '#FF8C42']
        )])
        
        fig_bar.update_layout(
            title="Problems by Type",
            xaxis_title="Problem Type",
            yaxis_title="Count",
            font=dict(size=12)
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Missing Files Detector",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Configure Streamlit to run locally
    if 'first_run' not in st.session_state:
        st.session_state.first_run = True
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
    }
    .main-header p {
        color: white;
        text-align: center;
        margin: 0.5rem 0 0 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Missing Files Detector</h1>
        <p>Comprehensive tool to detect missing files in folder structures</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize detector
    detector = StreamlitMissingFilesDetector()
    
    # Sidebar for controls
    with st.sidebar:
        st.markdown("### 🎛️ Controls")
        
        # Folder selection
        st.markdown("#### Select Folder to Scan")
        
        # Option to use current directory or browse
        if TKINTER_AVAILABLE:
            scan_options = ["Use textData folder", "Select custom folder", "Browse for folder"]
        else:
            scan_options = ["Use textData folder", "Select custom folder", "Browse for folder", "Upload ZIP folder", "Upload individual files"]
        
        scan_option = st.radio(
            "Scanning Options:",
            scan_options
        )
        
        selected_folder = None
        
        if scan_option == "Use textData folder":
            if os.path.exists("textData"):
                selected_folder = "textData"
                st.success("✅ textData folder found")
            else:
                st.error("❌ textData folder not found in current directory")
        
        elif scan_option == "Select custom folder":
            available_folders = detector.get_available_folders()
            if available_folders:
                selected_folder = st.selectbox(
                    "Available folders:",
                    available_folders
                )
            else:
                st.warning("No folders found in current directory")
        
        elif scan_option == "Browse for folder":
            st.markdown("**🗂️ Choose a folder to scan:**")
            
            # Show different instructions based on environment
            if TKINTER_AVAILABLE:
                st.info("💡 You can either enter the path manually or use the Browse button to select a folder.")
            else:
                st.info("🌐 Running in cloud mode. Please enter the folder path manually. You can use relative paths like 'data' or 'textData'.")
                st.warning("⚠️ Note: In cloud environment, you'll need to upload your data files first or use sample data paths.")
            
            # Initialize session state for selected folder
            if 'selected_folder_path' not in st.session_state:
                st.session_state.selected_folder_path = ""
            
            # Text input for manual path entry (full width)
            placeholder_text = "Enter folder path manually..." if not TKINTER_AVAILABLE else "Enter folder path manually or click Browse..."
            manual_path = st.text_input(
                "Folder path:",
                value=st.session_state.selected_folder_path,
                placeholder=placeholder_text,
                key="manual_path_input",
                help="Enter the full path to the folder you want to scan"
            )
            
            # Update session state when user types manually
            if manual_path != st.session_state.selected_folder_path:
                st.session_state.selected_folder_path = manual_path
            
            # Show current path status
            if st.session_state.selected_folder_path:
                st.markdown(f"**Current selection:** `{st.session_state.selected_folder_path}`")
            
            # IMPORTANT: Always check session state for folder selection
            if st.session_state.selected_folder_path:
                current_path = st.session_state.selected_folder_path
                if os.path.exists(current_path) and os.path.isdir(current_path):
                    selected_folder = current_path
            
            # Only show buttons if tkinter is available or for clear functionality
            if TKINTER_AVAILABLE:
                # Create two columns for buttons with better spacing
                col_browse, col_clear, col_spacer = st.columns([1, 1, 2])
                
                with col_browse:
                    # Browse button
                    if st.button("🗂️ Browse", help="Open folder selection dialog", type="secondary", use_container_width=True):
                        with st.spinner("Opening folder dialog..."):
                            selected_path = detector.select_folder_dialog()
                            if selected_path:
                                # Store in session state
                                st.session_state.selected_folder_path = selected_path
                                st.success(f"✅ Folder selected: {os.path.basename(selected_path)}")
                                # Note: Removed automatic rerun to prevent clearing the selection
                            else:
                                st.info("No folder selected")
                
                with col_clear:
                    # Clear button
                    if st.button("🗑️ Clear", help="Clear folder selection", type="secondary", use_container_width=True):
                        st.session_state.selected_folder_path = ""
                        st.info("Folder selection cleared")
            else:
                # Only show clear button in cloud mode
                col_clear, col_spacer = st.columns([1, 3])
                with col_clear:
                    if st.button("🗑️ Clear", help="Clear folder selection", type="secondary", use_container_width=True):
                        st.session_state.selected_folder_path = ""
                        st.info("Folder selection cleared")
                
                # Cloud-specific helper section
                st.markdown("**🌐 Cloud Environment Tips:**")
                with st.expander("💡 Common folder examples", expanded=False):
                    st.markdown("""
                    **Sample folder paths you can try:**
                    - `data` - if you have a data folder
                    - `textData` - common data folder name
                    - `documents` - for document folders
                    - `files` - generic files folder
                    - `.` - current directory (scan all files)
                    
                    **Note:** Make sure to upload your data files to the app first if testing with real data.
                    """)
                    
                    # Quick select buttons for common paths
                    st.markdown("**Quick select:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📁 textData", help="Select textData folder"):
                            st.session_state.selected_folder_path = "textData"
                            try:
                                st.rerun()
                            except:
                                st.experimental_rerun()
                    with col2:
                        if st.button("📁 data", help="Select data folder"):
                            st.session_state.selected_folder_path = "data"
                            try:
                                st.rerun()
                            except:
                                st.experimental_rerun()
                    with col3:
                        if st.button("📁 . (current)", help="Select current directory"):
                            st.session_state.selected_folder_path = "."
                            try:
                                st.rerun()
                            except:
                                st.experimental_rerun()
            
            # Final validation and feedback for Browse for folder option
            current_path = st.session_state.selected_folder_path
            if current_path:
                if os.path.exists(current_path) and os.path.isdir(current_path):
                    selected_folder = current_path
                    # Show folder info
                    try:
                        folder_info = os.listdir(current_path)
                        folder_count = len([item for item in folder_info if os.path.isdir(os.path.join(current_path, item))])
                        file_count = len([item for item in folder_info if os.path.isfile(os.path.join(current_path, item))])
                        st.success(f"✅ Valid folder: {folder_count} subfolders, {file_count} files")
                    except:
                        st.success("✅ Path exists and is accessible")
                elif os.path.exists(current_path):
                    st.error("❌ Path exists but is not a folder")
                    selected_folder = None
                else:
                    st.error("❌ Path does not exist")
                    selected_folder = None
        
        elif scan_option == "Upload ZIP folder" and not TKINTER_AVAILABLE:
            st.markdown("**📦 Upload ZIP File for Folder Analysis:**")
            st.info("🎯 Perfect solution! Upload a ZIP file containing your folders and files for complete analysis.")
            
            # Enhanced instructions for ZIP upload
            st.markdown("""
            **📋 How to prepare and upload your ZIP file:**
            1. **Create ZIP file:** Select your folder(s) on your PC and compress to ZIP
            2. **Upload ZIP:** Use the uploader below to upload your ZIP file
            3. **Auto-extract:** The app will extract and analyze the complete folder structure
            4. **Full analysis:** All folders, subfolders, and files will be scanned
            
            **✅ Advantages of ZIP upload:**
            - Preserves complete folder hierarchy
            - Handles any number of files and folders
            - Maintains original file organization
            - Works with complex nested structures
            
            **📁 Supported file types in ZIP:**
            All file types are supported - .md, .json, .log, .txt, .pdf, .docx, images, etc.
            """)
            
            uploaded_zip = st.file_uploader(
                "Choose a ZIP file to upload and extract",
                type=['zip'],
                help="Upload a ZIP file containing your folders and files for analysis"
            )
            
            if uploaded_zip is not None:
                import zipfile
                import tempfile
                import shutil
                
                try:
                    st.success(f"✅ ZIP file uploaded: {uploaded_zip.name} ({uploaded_zip.size:,} bytes)")
                    
                    # Create temporary directory for extraction
                    if 'temp_zip_dir' not in st.session_state:
                        st.session_state.temp_zip_dir = tempfile.mkdtemp(prefix="streamlit_zip_")
                    
                    extract_dir = st.session_state.temp_zip_dir
                    
                    # Extract ZIP file
                    with st.spinner("Extracting ZIP file..."):
                        zip_bytes = uploaded_zip.read()
                        
                        # Save ZIP file temporarily
                        zip_path = os.path.join(extract_dir, uploaded_zip.name)
                        with open(zip_path, 'wb') as f:
                            f.write(zip_bytes)
                        
                        # Extract ZIP contents
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_dir)
                        
                        # Remove the ZIP file itself, keep only extracted contents
                        os.remove(zip_path)
                    
                    st.success("🎉 ZIP file extracted successfully!")
                    
                    # Analyze extracted structure
                    total_folders = 0
                    total_files = 0
                    file_types = {'md': 0, 'json': 0, 'log': 0, 'other': 0}
                    
                    for root, dirs, files in os.walk(extract_dir):
                        total_folders += len(dirs)
                        total_files += len(files)
                        
                        for file in files:
                            ext = file.split('.')[-1].lower() if '.' in file else 'other'
                            if ext in ['md', 'markdown']:
                                file_types['md'] += 1
                            elif ext == 'json':
                                file_types['json'] += 1
                            elif ext == 'log':
                                file_types['log'] += 1
                            else:
                                file_types['other'] += 1
                    
                    # Display extraction summary
                    st.markdown("**📊 Extracted Structure Analysis:**")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Folders", total_folders)
                    with col2:
                        st.metric("Total Files", total_files)
                    with col3:
                        st.metric("MD Documents", file_types['md'])
                    with col4:
                        st.metric("JSON Files", file_types['json'])
                    
                    # Show detailed file type breakdown
                    with st.expander("📁 Detailed File Breakdown", expanded=False):
                        col_md, col_json, col_log, col_other = st.columns(4)
                        
                        with col_md:
                            st.write(f"**MD Files:** {file_types['md']}")
                        with col_json:
                            st.write(f"**JSON Files:** {file_types['json']}")
                        with col_log:
                            st.write(f"**Log Files:** {file_types['log']}")
                        with col_other:
                            st.write(f"**Other Files:** {file_types['other']}")
                    
                    # Show folder structure preview
                    with st.expander("🌳 Folder Structure Preview", expanded=False):
                        st.markdown("**Top-level folders and files:**")
                        try:
                            items = os.listdir(extract_dir)
                            folders = [item for item in items if os.path.isdir(os.path.join(extract_dir, item))]
                            files = [item for item in items if os.path.isfile(os.path.join(extract_dir, item))]
                            
                            if folders:
                                st.write("📁 **Folders:**")
                                for folder in sorted(folders)[:10]:  # Show first 10
                                    st.write(f"  • {folder}")
                                if len(folders) > 10:
                                    st.write(f"  ... and {len(folders) - 10} more folders")
                            
                            if files:
                                st.write("📄 **Files:**")
                                for file in sorted(files)[:10]:  # Show first 10
                                    st.write(f"  • {file}")
                                if len(files) > 10:
                                    st.write(f"  ... and {len(files) - 10} more files")
                        except Exception as e:
                            st.write(f"Error reading structure: {e}")
                    
                    # Set extracted directory as selected folder
                    selected_folder = extract_dir
                    st.success("🚀 Ready to scan extracted ZIP contents! Click 'Start Scan' to analyze.")
                    st.info(f"📂 Scanning path: {os.path.basename(extract_dir)} (extracted from {uploaded_zip.name})")
                    
                    # Clear ZIP contents option
                    col_clear, col_info = st.columns([1, 2])
                    with col_clear:
                        if st.button("🗑️ Clear ZIP contents", type="secondary"):
                            try:
                                shutil.rmtree(extract_dir)
                                del st.session_state.temp_zip_dir
                                st.success("ZIP contents cleared")
                                try:
                                    st.rerun()
                                except:
                                    st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error clearing ZIP contents: {e}")
                    
                    with col_info:
                        st.caption("💡 Upload a new ZIP file or clear to start over")
                
                except zipfile.BadZipFile:
                    st.error("❌ Invalid ZIP file. Please upload a valid ZIP archive.")
                except Exception as e:
                    st.error(f"❌ Error processing ZIP file: {e}")
            
            else:
                st.markdown("""
                **💡 How to create a ZIP file:**
                
                **Windows:**
                1. Right-click your folder
                2. Select "Send to" → "Compressed (zipped) folder"
                
                **Mac:**
                1. Right-click your folder
                2. Select "Compress [folder name]"
                
                **The ZIP file will contain your complete folder structure for analysis!**
                """)
        
        elif scan_option == "Upload individual files" and not TKINTER_AVAILABLE:
            st.markdown("**📎 Upload Individual Files (Alternative Method):**")
            st.info("💡 If you can't create a ZIP file, upload individual files. Less organized but still functional for testing.")
            
            uploaded_files = st.file_uploader(
                "Choose files to upload for testing",
                accept_multiple_files=True,
                type=['md', 'json', 'log', 'txt'],
                help="Upload some sample files to create a test folder structure"
            )
            
            if uploaded_files:
                st.success(f"✅ {len(uploaded_files)} files uploaded successfully!")
                
                # Create a temporary folder structure
                import tempfile
                import shutil
                
                if 'temp_upload_dir' not in st.session_state:
                    st.session_state.temp_upload_dir = tempfile.mkdtemp(prefix="streamlit_upload_")
                
                upload_dir = st.session_state.temp_upload_dir
                
                # Save uploaded files
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(upload_dir, uploaded_file.name)
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                
                st.info(f"📁 Files saved to temporary directory: {upload_dir}")
                st.markdown("**Files uploaded:**")
                for file in uploaded_files:
                    st.markdown(f"- {file.name} ({file.size} bytes)")
                
                # Set the upload directory as selected folder
                selected_folder = upload_dir
                st.success(f"✅ Ready to scan uploaded files in: {os.path.basename(upload_dir)}")
                
                if st.button("🗑️ Clear uploaded files"):
                    try:
                        shutil.rmtree(upload_dir)
                        del st.session_state.temp_upload_dir
                        st.success("Uploaded files cleared")
                        try:
                            st.rerun()
                        except:
                            # Fallback for older Streamlit versions
                            st.experimental_rerun()
                    except:
                        st.error("Error clearing uploaded files")
        
        # Scan button
        scan_button = st.button("🚀 Start Scan", type="primary", disabled=not selected_folder)
        
        # Debug information (can be removed in production)
        if selected_folder:
            st.sidebar.success(f"✅ Folder ready: {selected_folder}")
        else:
            st.sidebar.info("ℹ️ Select a folder to enable scanning")
        
        # Additional options
        st.markdown("#### 🔧 Options")
        show_valid_folders = st.checkbox("Show valid folders in results", value=True)
        auto_download = st.checkbox("Auto-download report", value=False)
    
    # Main content area
    if scan_button and selected_folder:
        st.markdown(f"### 🔍 Scanning: `{selected_folder}`")
        
        # Run the scan
        results = detector.run_scan(selected_folder)
        
        # Store results in session state for persistence
        st.session_state['scan_results'] = results
        st.session_state['show_valid_folders'] = show_valid_folders
        
        st.success("✅ Scan completed successfully!")
    
    # Display results if available
    if 'scan_results' in st.session_state:
        results = st.session_state['scan_results']
        show_valid = st.session_state.get('show_valid_folders', True)
        
        # Create visualizations
        create_visualizations(results)
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Summary", 
            "❌ Empty Folders", 
            "⚠️ JSON-Only Folders", 
            "🗂️ Empty Files Issues",
            "✅ Valid Folders" if show_valid else "📊 Export"
        ])
        
        with tab1:
            st.markdown("### 📋 Scan Summary")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                **Scan Information:**
                - **Folder Scanned:** `{results['root_path']}`
                - **Scan Date:** {datetime.fromisoformat(results['scan_date']).strftime('%Y-%m-%d %H:%M:%S')}
                - **Total Folders:** {results['summary']['total_scanned_folders']}
                - **Problematic Folders:** {results['summary']['total_problematic_folders']}
                """)
            
            with col2:
                # Download options
                st.markdown("**📥 Download Reports:**")
                
                # JSON report
                json_link = create_download_link(
                    results,
                    f"missing_files_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "📄 Download JSON Report"
                )
                st.markdown(json_link, unsafe_allow_html=True)
                
                # CSV report for problematic folders
                if results['summary']['total_problematic_folders'] > 0:
                    problematic_data = []
                    
                    for folder in results['empty_folders']:
                        problematic_data.append({
                            'Path': folder['path'],
                            'Issue Type': 'Empty Folder',
                            'Severity': folder.get('severity', 'high'),
                            'Issue': folder['issue'],
                            'MD Files': folder['file_counts']['md_files'],
                            'JSON Files': folder['file_counts']['json_files'],
                            'Empty Files': folder['file_counts'].get('empty_files', 0)
                        })
                    
                    for folder in results['json_only_folders']:
                        problematic_data.append({
                            'Path': folder['path'],
                            'Issue Type': 'JSON-Only Folder',
                            'Severity': folder.get('severity', 'high'),
                            'Issue': folder['issue'],
                            'MD Files': folder['file_counts']['md_files'],
                            'JSON Files': folder['file_counts']['json_files'],
                            'Empty Files': folder['file_counts'].get('empty_files', 0)
                        })
                    
                    for folder in results['folders_with_empty_files']:
                        problematic_data.append({
                            'Path': folder['path'],
                            'Issue Type': 'Empty Files Issue',
                            'Severity': folder.get('severity', 'medium'),
                            'Issue': folder['issue'],
                            'MD Files': folder['file_counts']['md_files'],
                            'JSON Files': folder['file_counts']['json_files'],
                            'Empty Files': folder['file_counts'].get('empty_files', 0)
                        })
                    
                    df = pd.DataFrame(problematic_data)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="📊 Download CSV Report",
                        data=csv,
                        file_name=f"problematic_folders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
        
        with tab2:
            display_folder_details(
                results['empty_folders'],
                "Empty Folders",
                "#FF6B6B",
                "❌"
            )
        
        with tab3:
            display_folder_details(
                results['json_only_folders'],
                "JSON-Only Folders",
                "#FFE66D",
                "⚠️"
            )
        
        with tab4:
            display_folder_details(
                results['folders_with_empty_files'],
                "Folders with Empty Files",
                "#FF8C42",
                "🗂️"
            )
        
        with tab5:
            if show_valid:
                display_folder_details(
                    results['valid_folders'],
                    "Valid Folders",
                    "#4ECDC4",
                    "✅"
                )
            else:
                st.markdown("### 📊 Export Options")
                st.info("Enable 'Show valid folders in results' in the sidebar to view valid folders here.")
    
    else:
        # Welcome message
        st.markdown("""
        ### 👋 Welcome to Missing Files Detector
        
        This application helps you identify folders that are missing important files in your directory structure.
        
        **What it detects:**
        - **Empty Folders**: Completely empty directories
        - **JSON-Only Folders**: Folders containing only JSON files without main content (.md files)
        - **Empty Files Issues**: Folders containing files that exist but are empty (0 bytes)
        - **Valid Folders**: Folders with proper content structure
        
        **Detection Criteria:**
        1. ✅ **Valid**: Contains .md files with actual content
        2. ❌ **Empty Folder**: No files at all
        3. ⚠️ **JSON-Only**: Only metadata files, no main content
        4. 🗂️ **Empty Files**: Contains files but some/all are empty (0 bytes)
        
        **How to use:**
        1. Select a folder to scan from the sidebar
        2. Click "Start Scan" to begin the analysis
        3. Review the results in the interactive dashboard
        4. Export reports for further analysis
        
        **🌐 Cloud Environment:**
        This app works both locally and in the cloud. In cloud mode, use manual path entry to specify folders.
        
        **Get started by selecting a folder in the sidebar! 👈**
        """)


if __name__ == "__main__":
    main()
