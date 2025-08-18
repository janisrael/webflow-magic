#!/usr/bin/env python3
"""
Setup script to create necessary directories for Pulse analytics
Run this once to set up the directory structure
"""

import os

def setup_pulse_directories():
    """
    Create necessary directories for Pulse analytics
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Directories to create
    directories = [
        os.path.join(base_dir, 'output'),
        os.path.join(base_dir, 'output', 'pulse'),
        os.path.join(base_dir, 'services'),
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")
    
    # Create __init__.py files for Python packages
    init_files = [
        os.path.join(base_dir, 'services', '__init__.py'),
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# Services package\n')
            print(f"✅ Created __init__.py: {init_file}")
        else:
            print(f"📄 __init__.py already exists: {init_file}")
    
    print("\n🎉 Pulse directory setup complete!")
    print("You can now use the Pulse analytics feature.")

if __name__ == "__main__":
    setup_pulse_directories()