#!/usr/bin/env python3
"""
DJ Harmonic Toolkit - Unified Application
Combines harmonic mixing, library scanning, and file renaming into one tool
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import re
import hashlib
import time
import threading
import subprocess
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

class DJToolkit:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DJ Harmonic Toolkit")
        self.root.geometry("1000x700")
        
        # Initialize components
        self.mixxx_db_path = os.path.expanduser("~/.mixxx/mixxxdb.sqlite")
        self.music_dir = Path("/home/tim/Music")
        self.scanner_db_path = Path.home() / ".music_scanner.db"
        self.audio_extensions = {'.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', '.wma'}
        
        # Initialize harmonic compatibility
        self.init_harmonic_compatibility()
        
        # Initialize scanner database
        self.init_scanner_db()
        
        # Setup UI
        self.setup_ui()
    
    def init_harmonic_compatibility(self):
        """Initialize circle of fifths compatibility mapping"""
        # Traditional notation compatibility
        self.harmonic_compatibility = {
            # Major keys
            'C': ['C', 'F', 'G', 'Am', 'Dm', 'Em'],
            'C♯': ['C♯', 'F♯', 'G♯', 'A♯m', 'D♯m', 'E♯m'],
            'D♭': ['D♭', 'G♭', 'A♭', 'B♭m', 'E♭m', 'Fm'],
            'D': ['D', 'G', 'A', 'Bm', 'Em', 'F♯m'],
            'E♭': ['E♭', 'A♭', 'B♭', 'Cm', 'Fm', 'Gm'],
            'E': ['E', 'A', 'B', 'C♯m', 'F♯m', 'G♯m'],
            'F': ['F', 'B♭', 'C', 'Dm', 'Gm', 'Am'],
            'F♯': ['F♯', 'B', 'C♯', 'D♯m', 'G♯m', 'A♯m'],
            'G♭': ['G♭', 'B', 'D♭', 'E♭m', 'A♭m', 'B♭m'],
            'G': ['G', 'C', 'D', 'Em', 'Am', 'Bm'],
            'A♭': ['A♭', 'D♭', 'E♭', 'Fm', 'B♭m', 'Cm'],
            'A': ['A', 'D', 'E', 'F♯m', 'Bm', 'C♯m'],
            'B♭': ['B♭', 'E♭', 'F', 'Gm', 'Cm', 'Dm'],
            'B': ['B', 'E', 'F♯', 'G♯m', 'C♯m', 'D♯m'],
            
            # Minor keys
            'Am': ['Am', 'Dm', 'Em', 'C', 'F', 'G'],
            'A♯m': ['A♯m', 'D♯m', 'E♯m', 'C♯', 'F♯', 'G♯'],
            'B♭m': ['B♭m', 'E♭m', 'Fm', 'D♭', 'G♭', 'A♭'],
            'Bm': ['Bm', 'Em', 'F♯m', 'D', 'G', 'A'],
            'Cm': ['Cm', 'Fm', 'Gm', 'E♭', 'A♭', 'B♭'],
            'C♯m': ['C♯m', 'F♯m', 'G♯m', 'E', 'A', 'B'],
            'Dm': ['Dm', 'Gm', 'Am', 'F', 'B♭', 'C'],
            'D♯m': ['D♯m', 'G♯m', 'A♯m', 'F♯', 'B', 'C♯'],
            'E♭m': ['E♭m', 'A♭m', 'B♭m', 'G♭', 'B', 'D♭'],
            'Em': ['Em', 'Am', 'Bm', 'G', 'C', 'D'],
            'Fm': ['Fm', 'B♭m', 'Cm', 'A♭', 'D♭', 'E♭'],
            'F♯m': ['F♯m', 'Bm', 'C♯m', 'A', 'D', 'E'],
            'Gm': ['Gm', 'Cm', 'Dm', 'B♭', 'E♭', 'F'],
            'G♯m': ['G♯m', 'C♯m', 'D♯m', 'B', 'E', 'F♯'],
        }
        
        # Camelot wheel mapping (traditional to Camelot)
        self.camelot_mapping = {
            # Major keys (B side)
            'C': '8B', 'D♭': '3B', 'D': '10B', 'E♭': '5B', 'E': '12B', 'F': '7B',
            'F♯': '2B', 'G♭': '2B', 'G': '9B', 'A♭': '4B', 'A': '11B', 'B♭': '6B', 'B': '1B',
            # Minor keys (A side)
            'Am': '8A', 'B♭m': '3A', 'Bm': '10A', 'Cm': '5A', 'C♯m': '12A', 'Dm': '7A',
            'D♯m': '2A', 'E♭m': '2A', 'Em': '9A', 'Fm': '4A', 'F♯m': '11A', 'Gm': '6A', 'G♯m': '1A'
        }
        
        # Reverse mapping (Camelot to traditional)
        self.camelot_to_traditional = {v: k for k, v in self.camelot_mapping.items()}
        
        # Add alternative notations
        self.camelot_to_traditional.update({
            '8B (C)': 'C', '3B (D♭)': 'D♭', '10B (D)': 'D', '5B (E♭)': 'E♭',
            '12B (E)': 'E', '7B (F)': 'F', '2B (F♯/G♭)': 'F♯', '9B (G)': 'G',
            '4B (A♭)': 'A♭', '11B (A)': 'A', '6B (B♭)': 'B♭', '1B (B)': 'B',
            '8A (Am)': 'Am', '3A (B♭m)': 'B♭m', '10A (Bm)': 'Bm', '5A (Cm)': 'Cm',
            '12A (C♯m)': 'C♯m', '7A (Dm)': 'Dm', '2A (D♯m/E♭m)': 'D♯m', '9A (Em)': 'Em',
            '4A (Fm)': 'Fm', '11A (F♯m)': 'F♯m', '6A (Gm)': 'Gm', '1A (G♯m)': 'G♯m'
        })
    
    def normalize_key(self, key):
        """Normalize key notation to traditional format"""
        if not key:
            return None
        
        # Handle special cases
        key = key.strip()
        if key == 'D♯m/E♭m':
            return 'D♯m'
        if key == 'F♯/G♭':
            return 'F♯'
        
        # Convert Camelot notation to traditional
        if key in self.camelot_to_traditional:
            return self.camelot_to_traditional[key]
        
        return key
    
    def get_all_compatible_keys(self, input_key):
        """Get all compatible keys including different notations"""
        normalized_key = self.normalize_key(input_key)
        if not normalized_key:
            return []
        
        # Get traditional compatible keys
        compatible_traditional = self.harmonic_compatibility.get(normalized_key, [normalized_key])
        
        # Add all possible notations for each compatible key
        all_compatible = set(compatible_traditional)
        
        # Add Camelot notations
        for trad_key in compatible_traditional:
            if trad_key in self.camelot_mapping:
                camelot_key = self.camelot_mapping[trad_key]
                all_compatible.add(camelot_key)
                all_compatible.add(f"{camelot_key} ({trad_key})")
        
        # Add alternative spellings
        for key in list(all_compatible):
            if key == 'D♯m':
                all_compatible.add('D♯m/E♭m')
                all_compatible.add('E♭m')
            elif key == 'F♯':
                all_compatible.add('F♯/G♭')
                all_compatible.add('G♭')
        
        return list(all_compatible)
    
    def init_scanner_db(self):
        """Initialize scanner database"""
        conn = sqlite3.connect(self.scanner_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scanned_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                file_hash TEXT,
                file_size INTEGER,
                last_modified REAL,
                bpm REAL,
                key TEXT,
                duration REAL,
                artist TEXT,
                title TEXT,
                album TEXT,
                genre TEXT,
                scan_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                in_mixxx INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                files_found INTEGER,
                new_files INTEGER,
                updated_files INTEGER,
                scan_duration REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.setup_harmonic_tab()
        self.setup_scanner_tab()
        self.setup_renamer_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="DJ Harmonic Toolkit Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
        
        # Menu bar
        self.setup_menu()
    
    def setup_menu(self):
        """Setup application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Quick Scan", command=self.quick_scan)
        tools_menu.add_command(label="Refresh Mixxx DB", command=self.refresh_mixxx_db)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_harmonic_tab(self):
        """Setup harmonic mixing tab"""
        harmonic_frame = ttk.Frame(self.notebook)
        self.notebook.add(harmonic_frame, text="🎵 Harmonic Mixing")
        
        # Current track input
        input_frame = ttk.LabelFrame(harmonic_frame, text="Current Track", padding="10")
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # BPM and Key inputs
        ttk.Label(input_frame, text="BPM:").grid(row=0, column=0, sticky=tk.W)
        self.bpm_var = tk.StringVar(value="120")
        bpm_entry = ttk.Entry(input_frame, textvariable=self.bpm_var, width=10)
        bpm_entry.grid(row=0, column=1, padx=(5, 20))
        
        ttk.Label(input_frame, text="Key:").grid(row=0, column=2, sticky=tk.W)
        self.key_var = tk.StringVar(value="C")
        key_combo = ttk.Combobox(input_frame, textvariable=self.key_var, width=8)
        key_combo['values'] = list(self.harmonic_compatibility.keys())
        key_combo.grid(row=0, column=3, padx=(5, 20))
        
        ttk.Button(input_frame, text="Find Compatible Tracks", 
                  command=self.find_compatible_tracks).grid(row=0, column=4, padx=(10, 0))
        
        # Results frame
        results_frame = ttk.LabelFrame(harmonic_frame, text="Compatible Tracks", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview for results
        columns = ('Artist', 'Title', 'BPM', 'Key', 'Duration', 'Compatibility')
        self.harmonic_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        for col in columns:
            self.harmonic_tree.heading(col, text=col)
        
        self.harmonic_tree.column('Artist', width=150)
        self.harmonic_tree.column('Title', width=200)
        self.harmonic_tree.column('BPM', width=60)
        self.harmonic_tree.column('Key', width=50)
        self.harmonic_tree.column('Duration', width=60)
        self.harmonic_tree.column('Compatibility', width=80)
        
        # Scrollbar for harmonic tree
        harmonic_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.harmonic_tree.yview)
        self.harmonic_tree.configure(yscrollcommand=harmonic_scrollbar.set)
        
        self.harmonic_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        harmonic_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_scanner_tab(self):
        """Setup library scanner tab"""
        scanner_frame = ttk.Frame(self.notebook)
        self.notebook.add(scanner_frame, text="📁 Library Scanner")
        
        # Directory selection
        dir_frame = ttk.LabelFrame(scanner_frame, text="Music Directory", padding="10")
        dir_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.music_dir_var = tk.StringVar(value=str(self.music_dir))
        ttk.Entry(dir_frame, textvariable=self.music_dir_var, width=60).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(dir_frame, text="Browse", command=self.browse_music_dir).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(dir_frame, text="Scan Library", command=self.start_library_scan).pack(side=tk.LEFT)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(scanner_frame, text="Scan Progress", padding="10")
        progress_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.scan_progress_var = tk.StringVar(value="Ready to scan")
        ttk.Label(progress_frame, textvariable=self.scan_progress_var).pack(anchor=tk.W)
        
        self.scan_progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.scan_progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Results frame
        scan_results_frame = ttk.LabelFrame(scanner_frame, text="Scan Results", padding="10")
        scan_results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.scan_results_text = tk.Text(scan_results_frame, height=15, width=70)
        scan_scrollbar = ttk.Scrollbar(scan_results_frame, orient=tk.VERTICAL, command=self.scan_results_text.yview)
        self.scan_results_text.configure(yscrollcommand=scan_scrollbar.set)
        
        self.scan_results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scan_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_renamer_tab(self):
        """Setup file renamer tab"""
        renamer_frame = ttk.Frame(self.notebook)
        self.notebook.add(renamer_frame, text="✏️ File Renamer")
        
        # Directory selection for renamer
        rename_dir_frame = ttk.LabelFrame(renamer_frame, text="Directory to Rename", padding="10")
        rename_dir_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.rename_dir_var = tk.StringVar(value=str(self.music_dir))
        ttk.Entry(rename_dir_frame, textvariable=self.rename_dir_var, width=60).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(rename_dir_frame, text="Browse", command=self.browse_rename_dir).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(rename_dir_frame, text="Preview Renames", command=self.preview_renames).pack(side=tk.LEFT)
        
        # Options frame
        options_frame = ttk.LabelFrame(renamer_frame, text="Options", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.use_metadata_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Use Mixxx metadata when available", 
                       variable=self.use_metadata_var).pack(anchor=tk.W)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(renamer_frame, text="Rename Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview for rename preview
        rename_columns = ('Original', 'New Name', 'Status')
        self.rename_tree = ttk.Treeview(preview_frame, columns=rename_columns, show='headings', height=12)
        
        for col in rename_columns:
            self.rename_tree.heading(col, text=col)
        
        self.rename_tree.column('Original', width=300)
        self.rename_tree.column('New Name', width=300)
        self.rename_tree.column('Status', width=100)
        
        # Scrollbars for rename tree
        rename_v_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.rename_tree.yview)
        rename_h_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.rename_tree.xview)
        self.rename_tree.configure(yscrollcommand=rename_v_scrollbar.set, xscrollcommand=rename_h_scrollbar.set)
        
        self.rename_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rename_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        rename_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Control buttons
        button_frame = ttk.Frame(renamer_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Apply Renames", command=self.apply_renames).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Clear Preview", command=self.clear_rename_preview).pack(side=tk.LEFT)
        
    # ===== HARMONIC MIXING METHODS =====
    
    def find_compatible_tracks(self):
        """Find tracks compatible with current BPM and key"""
        try:
            bpm = float(self.bpm_var.get())
            key = self.key_var.get()
            
            if not key:
                messagebox.showerror("Error", "Please select a key")
                return
            
            self.status_var.set("Searching for compatible tracks...")
            self.root.update()
            
            # Clear previous results
            for item in self.harmonic_tree.get_children():
                self.harmonic_tree.delete(item)
            
            # Get compatible tracks
            tracks = self.get_compatible_tracks(bpm, key)
            
            if not tracks:
                self.status_var.set("No compatible tracks found")
                return
            
            # Populate results
            for track in tracks:
                artist, title, album, track_bpm, track_key, duration, location = track
                
                # Determine compatibility level
                normalized_current = self.normalize_key(key)
                normalized_track = self.normalize_key(track_key)
                
                if normalized_track == normalized_current:
                    compatibility = "Perfect"
                elif normalized_track in self.get_all_compatible_keys(normalized_current):
                    compatibility = "Good"
                else:
                    compatibility = "OK"
                
                self.harmonic_tree.insert('', tk.END, values=(
                    artist or "Unknown",
                    title or "Unknown",
                    f"{track_bpm:.1f}" if track_bpm else "?",
                    track_key or "?",
                    self.format_duration(duration),
                    compatibility
                ))
            
            self.status_var.set(f"Found {len(tracks)} compatible tracks")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid BPM number")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def get_compatible_tracks(self, current_bpm, current_key, bpm_tolerance=2):
        """Find tracks compatible with current BPM and key"""
        if not os.path.exists(self.mixxx_db_path):
            return []
        
        try:
            conn = sqlite3.connect(self.mixxx_db_path)
            cursor = conn.cursor()
            
            # Get all compatible keys (including different notations)
            compatible_keys = self.get_all_compatible_keys(current_key)
            
            if not compatible_keys:
                compatible_keys = [current_key]
            
            # Build query for BPM range and compatible keys
            bpm_min = current_bpm - bpm_tolerance
            bpm_max = current_bpm + bpm_tolerance
            
            placeholders = ','.join(['?' for _ in compatible_keys])
            query = f"""
                SELECT artist, title, album, bpm, key, duration, location
                FROM library 
                WHERE bpm BETWEEN ? AND ? 
                AND key IN ({placeholders})
                AND mixxx_deleted = 0
                ORDER BY 
                    CASE WHEN key = ? THEN 0 ELSE 1 END,
                    ABS(bpm - ?) ASC
                LIMIT 50
            """
            
            params = [bpm_min, bpm_max] + compatible_keys + [current_key, current_bpm]
            cursor.execute(query, params)
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"Database error: {e}")
            return []
    
    def format_duration(self, seconds):
        """Convert seconds to MM:SS format"""
        if not seconds:
            return "0:00"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    # ===== LIBRARY SCANNER METHODS =====
    
    def browse_music_dir(self):
        """Browse for music directory"""
        directory = filedialog.askdirectory(initialdir=self.music_dir_var.get())
        if directory:
            self.music_dir_var.set(directory)
            self.music_dir = Path(directory)
    
    def start_library_scan(self):
        """Start library scanning in background thread"""
        def scan_thread():
            try:
                self.scan_results_text.delete(1.0, tk.END)
                self.scan_results_text.insert(tk.END, "Starting library scan...\n")
                
                directory = Path(self.music_dir_var.get())
                results = self.scan_music_library(directory)
                
                self.scan_results_text.insert(tk.END, f"\nScan Results:\n")
                self.scan_results_text.insert(tk.END, f"Files processed: {results['files_found']}\n")
                self.scan_results_text.insert(tk.END, f"New files: {results['new_files']}\n")
                self.scan_results_text.insert(tk.END, f"Updated files: {results['updated_files']}\n")
                self.scan_results_text.insert(tk.END, f"Duration: {results['scan_duration']:.2f} seconds\n")
                
                self.scan_progress_var.set("Scan complete!")
                
            except Exception as e:
                self.scan_results_text.insert(tk.END, f"Error during scan: {e}\n")
                self.scan_progress_var.set("Scan failed!")
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def scan_progress_callback(self, current, total, filename):
        """Progress callback for scanning"""
        progress = (current / total) * 100
        self.scan_progress_bar['value'] = progress
        self.scan_progress_var.set(f"Processing {current}/{total}: {Path(filename).name}")
        self.root.update()
    
    def scan_music_library(self, directory):
        """Scan music library for new files"""
        start_time = time.time()
        files_found = 0
        new_files = 0
        updated_files = 0
        
        # Get all audio files recursively
        audio_files = []
        for ext in self.audio_extensions:
            audio_files.extend(directory.rglob(f"*{ext}"))
            audio_files.extend(directory.rglob(f"*{ext.upper()}"))
        
        total_files = len(audio_files)
        
        conn = sqlite3.connect(self.scanner_db_path)
        cursor = conn.cursor()
        
        for i, file_path in enumerate(audio_files):
            self.scan_progress_callback(i + 1, total_files, str(file_path))
            
            try:
                # Get file stats
                stat = file_path.stat()
                file_size = stat.st_size
                last_modified = stat.st_mtime
                file_hash = self.get_file_hash(file_path)
                
                # Check if file exists in our database
                cursor.execute(
                    "SELECT file_hash, last_modified FROM scanned_files WHERE file_path = ?",
                    (str(file_path),)
                )
                existing = cursor.fetchone()
                
                needs_analysis = False
                if not existing:
                    new_files += 1
                    needs_analysis = True
                elif existing[0] != file_hash or existing[1] != last_modified:
                    updated_files += 1
                    needs_analysis = True
                
                if needs_analysis:
                    analysis = self.analyze_audio_file(file_path)
                    
                    if analysis:
                        cursor.execute('''
                            INSERT OR REPLACE INTO scanned_files 
                            (file_path, file_hash, file_size, last_modified, 
                             bpm, key, duration, artist, title, album, genre)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            str(file_path), file_hash, file_size, last_modified,
                            analysis['bpm'], analysis['key'], analysis['duration'],
                            analysis['artist'], analysis['title'], analysis['album'],
                            analysis['genre']
                        ))
                
                files_found += 1
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        # Record scan session
        scan_duration = time.time() - start_time
        cursor.execute('''
            INSERT INTO scan_sessions (files_found, new_files, updated_files, scan_duration)
            VALUES (?, ?, ?, ?)
        ''', (files_found, new_files, updated_files, scan_duration))
        
        conn.commit()
        conn.close()
        
        return {
            'files_found': files_found,
            'new_files': new_files,
            'updated_files': updated_files,
            'scan_duration': scan_duration
        }
    
    def get_file_hash(self, file_path):
        """Generate MD5 hash of file for change detection"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                # Read first and last 64KB for speed
                hash_md5.update(f.read(65536))
                f.seek(-65536, 2)
                hash_md5.update(f.read(65536))
            return hash_md5.hexdigest()
        except:
            return None
    
    def analyze_audio_file(self, file_path):
        """Analyze audio file using ffprobe for metadata"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return None
            
            data = json.loads(result.stdout)
            format_info = data.get('format', {})
            tags = format_info.get('tags', {})
            
            # Extract metadata (case-insensitive)
            def get_tag(tag_name):
                for key, value in tags.items():
                    if key.lower() == tag_name.lower():
                        return value
                return None
            
            return {
                'duration': float(format_info.get('duration', 0)),
                'artist': get_tag('artist') or get_tag('albumartist'),
                'title': get_tag('title'),
                'album': get_tag('album'),
                'genre': get_tag('genre'),
                'bpm': None,  # Would need specialized tool
                'key': None   # Would need specialized tool
            }
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    # ===== FILE RENAMER METHODS =====
    
    def browse_rename_dir(self):
        """Browse for directory to rename"""
        directory = filedialog.askdirectory(initialdir=self.rename_dir_var.get())
        if directory:
            self.rename_dir_var.set(directory)
    
    def preview_renames(self):
        """Preview file renames"""
        def preview_thread():
            try:
                self.status_var.set("Analyzing files for rename...")
                self.root.update()
                
                directory = Path(self.rename_dir_var.get())
                self.renames = self.get_rename_preview(directory)
                
                # Clear previous results
                for item in self.rename_tree.get_children():
                    self.rename_tree.delete(item)
                
                # Populate results
                for rename_info in self.renames:
                    original = rename_info['original_name']
                    new_name = rename_info['new_name']
                    
                    # Check if target would conflict
                    status = "Ready"
                    if rename_info['new_path'].exists():
                        status = "Conflict"
                    
                    self.rename_tree.insert('', tk.END, values=(original, new_name, status))
                
                self.status_var.set(f"Found {len(self.renames)} files to rename")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error during preview: {str(e)}")
                self.status_var.set("Preview failed")
        
        threading.Thread(target=preview_thread, daemon=True).start()
    
    def get_rename_preview(self, directory):
        """Get preview of what files would be renamed"""
        renames = []
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.audio_extensions:
                new_name = self.generate_clean_filename(file_path)
                
                if new_name != file_path.name:
                    renames.append({
                        'original_path': file_path,
                        'original_name': file_path.name,
                        'new_name': new_name,
                        'new_path': file_path.parent / new_name
                    })
        
        return renames
    
    def generate_clean_filename(self, file_path):
        """Generate a clean filename for the given file"""
        original_name = file_path.stem
        extension = file_path.suffix
        
        artist, title = None, None
        
        # Try to get metadata from Mixxx first
        if self.use_metadata_var.get():
            artist, title = self.get_metadata_from_mixxx(file_path)
        
        # If no metadata, extract from filename
        if not artist or not title:
            extracted_artist, extracted_title = self.extract_artist_title(original_name)
            artist = artist or extracted_artist
            title = title or extracted_title
        
        # Generate clean filename
        if artist and title:
            clean_name = f"{artist} - {title}"
        elif title:
            clean_name = title
        else:
            clean_name = self.clean_filename_part(original_name)
        
        # Remove invalid filename characters
        clean_name = re.sub(r'[<>:"/\\|?*]', '', clean_name)
        clean_name = clean_name.strip()
        
        return clean_name + extension
    
    def get_metadata_from_mixxx(self, file_path):
        """Try to get artist/title from Mixxx database"""
        if not os.path.exists(self.mixxx_db_path):
            return None, None
        
        try:
            conn = sqlite3.connect(self.mixxx_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT l.artist, l.title 
                FROM library l
                JOIN track_locations tl ON l.location = tl.id
                WHERE tl.location LIKE ?
            """, (f"%{file_path.name}%",))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0], result[1]
            
        except Exception as e:
            print(f"Error querying Mixxx database: {e}")
        
        return None, None
    
    def extract_artist_title(self, filename_without_ext):
        """Try to extract artist and title from filename"""
        cleaned = self.clean_filename_part(filename_without_ext)
        
        # Artist extraction patterns
        artist_patterns = [
            r'^(.+?)\s*[-–—]\s*(.+)$',  # "Artist - Title"
            r'^(.+?)_-_(.+)$',          # "Artist_-_Title"
            r'^(.+?)\s+by\s+(.+)$',     # "Artist by Title"
        ]
        
        # Try each pattern
        for pattern in artist_patterns:
            match = re.match(pattern, cleaned)
            if match:
                part1, part2 = match.groups()
                part1 = self.clean_filename_part(part1)
                part2 = self.clean_filename_part(part2)
                
                # Heuristic: shorter part is usually artist (unless very short)
                if len(part1) < len(part2) and len(part1) > 2:
                    return part1, part2  # artist, title
                elif len(part2) < len(part1) and len(part2) > 2:
                    return part2, part1  # artist, title
                else:
                    return part1, part2  # assume first is artist
        
        # If no pattern matches, return cleaned filename as title
        return "", cleaned
    
    def clean_filename_part(self, text):
        """Clean up a filename part (artist or title)"""
        if not text:
            return ""
        
        # Common patterns to clean up
        cleanup_patterns = [
            (r'^(\d{1,3}[\.\-_\s]*)', ''),  # Remove track numbers
            (r'^(track[\s\-_]*\d*[\s\-_]*)', '', re.IGNORECASE),  # Remove "track"
            (r'[_]+', ' '),  # Replace underscores with spaces
            (r'\s+', ' '),   # Multiple spaces to single
            (r'\s*[\(\[]*(320|128|192|256|kbps|mp3|flac|wav|official|audio|hq|hd)[\)\]]*\s*', '', re.IGNORECASE),
            (r'\s*[-_]+\s*', ' - '),  # Clean separators
            (r'\s*[–—]\s*', ' - '),   # Unicode dashes
            (r'^[\s\-_]+|[\s\-_]+$', ''),  # Trim
        ]
        
        # Apply cleanup patterns
        for pattern, replacement, *flags in cleanup_patterns:
            flag = flags[0] if flags else 0
            text = re.sub(pattern, replacement, text, flags=flag)
        
        # Smart capitalization
        return self.smart_capitalize(text.strip())
    
    def smart_capitalize(self, text):
        """Smart capitalization for music titles"""
        if not text:
            return ""
        
        lowercase_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 
                          'in', 'of', 'on', 'or', 'the', 'to', 'up', 'vs', 'with'}
        uppercase_words = {'dj', 'mc', 'uk', 'usa', 'nyc', 'la', 'sf', 'tv', 'fm', 'am'}
        
        words = text.split()
        result = []
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            
            if word_lower in uppercase_words:
                result.append(word.upper())
            elif i > 0 and word_lower in lowercase_words:
                result.append(word_lower)
            else:
                if word:
                    result.append(word[0].upper() + word[1:])
        
        return ' '.join(result)
    
    def apply_renames(self):
        """Apply the file renames"""
        if not hasattr(self, 'renames') or not self.renames:
            messagebox.showwarning("Warning", "No renames to perform. Run preview first.")
            return
        
        # Confirm with user
        result = messagebox.askyesno(
            "Confirm Rename", 
            f"This will rename {len(self.renames)} files. This cannot be undone. Continue?"
        )
        
        if not result:
            return
        
        def rename_thread():
            try:
                self.status_var.set("Renaming files...")
                success_count = 0
                error_count = 0
                
                for i, rename_info in enumerate(self.renames):
                    try:
                        original_path = rename_info['original_path']
                        new_path = rename_info['new_path']
                        
                        # Check if target already exists
                        if new_path.exists():
                            error_count += 1
                            item = self.rename_tree.get_children()[i]
                            self.rename_tree.set(item, 'Status', 'Conflict')
                            continue
                        
                        # Rename the file
                        original_path.rename(new_path)
                        success_count += 1
                        
                        # Update tree
                        item = self.rename_tree.get_children()[i]
                        self.rename_tree.set(item, 'Status', 'Renamed')
                        
                    except Exception as e:
                        error_count += 1
                        item = self.rename_tree.get_children()[i]
                        self.rename_tree.set(item, 'Status', 'Failed')
                
                message = f"Renamed {success_count} files"
                if error_count > 0:
                    message += f", {error_count} errors"
                
                self.status_var.set(message)
                messagebox.showinfo("Complete", message)
                
            except Exception as e:
                messagebox.showerror("Error", f"Error during rename: {str(e)}")
                self.status_var.set("Rename failed")
        
        threading.Thread(target=rename_thread, daemon=True).start()
    
    def clear_rename_preview(self):
        """Clear rename preview"""
        for item in self.rename_tree.get_children():
            self.rename_tree.delete(item)
        if hasattr(self, 'renames'):
            self.renames = []
        self.status_var.set("Preview cleared")
    
    # ===== UTILITY METHODS =====
    
    def quick_scan(self):
        """Quick scan of music library"""
        self.notebook.select(1)  # Switch to scanner tab
        self.start_library_scan()
    
    def refresh_mixxx_db(self):
        """Refresh Mixxx database connection"""
        self.status_var.set("Mixxx database connection refreshed")
        messagebox.showinfo("Info", "Database connection refreshed. New tracks should now appear in searches.")
    
    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog coming soon!")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """DJ Harmonic Toolkit v1.0
        
A comprehensive suite of tools for DJs:
• Harmonic mixing with circle of fifths
• Music library scanning and analysis  
• Intelligent file renaming

Integrates with Mixxx DJ software.

Created for the DJ community."""
        
        messagebox.showinfo("About DJ Harmonic Toolkit", about_text)
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = DJToolkit()
    app.run()
