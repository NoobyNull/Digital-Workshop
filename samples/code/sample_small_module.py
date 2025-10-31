#!/usr/bin/env python3
"""
Sample Small Module - Under 500 lines
This module demonstrates a well-structured, small Python module.
"""

import os
import sys
from typing import List, Dict, Optional


class DataProcessor:
    """A simple data processor class."""
    
    def __init__(self, name: str):
        """Initialize the data processor.
        
        Args:
            name: Name of the processor
        """
        self.name = name
        self.data: List[str] = []
    
    def add_data(self, item: str) -> None:
        """Add an item to the data list.
        
        Args:
            item: String item to add
        """
        self.data.append(item)
    
    def get_data(self) -> List[str]:
        """Get all data items.
        
        Returns:
            List of data items
        """
        return self.data.copy()
    
    def clear_data(self) -> None:
        """Clear all data."""
        self.data.clear()


def process_files(directory: str) -> Dict[str, int]:
    """Process files in a directory.
    
    Args:
        directory: Path to directory
        
    Returns:
        Dictionary mapping filenames to line counts
    """
    results = {}
    
    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    results[filename] = len(lines)
    except OSError:
        pass
    
    return results


def main():
    """Main function."""
    processor = DataProcessor("test")
    
    # Add some sample data
    processor.add_data("item1")
    processor.add_data("item2")
    processor.add_data("item3")
    
    print(f"Processor: {processor.name}")
    print(f"Data: {processor.get_data()}")
    
    # Process current directory
    results = process_files(".")
    print(f"Files processed: {len(results)}")


if __name__ == "__main__":
    main()