import os
import logging
from typing import Callable, List

def process_workdir(workdir: str, palette_dir: str, processors: List[Callable]) -> None:
    """
    Process the entire workdir containing collection directories
    
    Args:
        workdir: Path to working directory
        palette_dir: Directory containing palette files
        processors: List of processing functions to run on each granule
    """
    if not os.path.exists(workdir):
        logging.error(f"Working directory {workdir} does not exist")
        return

    # Process each collection directory
    # Sort directories alphabetically
    for item in sorted(os.listdir(workdir)):
        collection_dir = os.path.join(workdir, item)
        if os.path.isdir(collection_dir):
            process_collection_dir(collection_dir, palette_dir, processors)


def process_collection_dir(collection_dir: str, palette_dir: str, processors: List[Callable]) -> None:
    """
    Process a single collection directory
    
    Args:
        collection_dir: Path to collection directory
        palette_dir: Directory containing palette files
        processors: List of processing functions to run on each granule
    """
    collection_name = os.path.basename(collection_dir)
    config_file = os.path.join(collection_dir, f"{collection_name}.cfg")
    
    if not os.path.exists(config_file):
        logging.warning(f"Config file not found for {collection_name}")
        return
        
    # Process each granule subdirectory
    for item in os.listdir(collection_dir):
        item_path = os.path.join(collection_dir, item)
        if os.path.isdir(item_path):
            print(f"Processing directory: {item_path}")
            
            # Run each processor function
            for process_func in processors:
                process_func(item_path, config_file, palette_dir)
            
            print() 