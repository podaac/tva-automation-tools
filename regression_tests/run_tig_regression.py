import argparse
import logging
import subprocess
import os
from typing import Tuple
from regression_base import process_workdir

def run_tig_process(input_file: str, output_dir: str, config_file: str, palette_dir: str) -> Tuple[str, int]:
    """
    Run the TIG process on a single granule file and capture output
    
    Args:
        input_file: Path to input granule file
        output_dir: Directory to store TIG output
        config_file: Path to config file
        palette_dir: Directory containing palette files
        
    Returns:
        Tuple of (output string, return code) from TIG process
    """
    try:
        cmd = [
            'tig',
            '--input_file', input_file,
            '--output_dir', output_dir, 
            '--config_file', config_file,
            '--palette_dir', palette_dir
        ]
        
        # Print the command being executed
        print("\nExecuting TIG command:")
        print(f"Input file: {input_file}")
        print(f"Output directory: {output_dir}")
        print(f"Config file: {config_file}")
        print(f"Palette directory: {palette_dir}")
        print(" ".join(cmd))
        print()
        result = subprocess.run(cmd,
                              capture_output=True,
                              text=True,
                              check=True)
        output = result.stdout + "\n" + result.stderr if result.stderr else result.stdout
        return output, result.returncode
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running TIG command: {e.stderr}")
        output = f"STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        return output, e.returncode


def process_granule_dir_tig(granule_dir: str, config_file: str, palette_dir: str) -> None:
    """
    Process a single granule directory for TIG
    
    Args:
        granule_dir: Path to granule directory
        config_file: Path to config file
        palette_dir: Directory containing palette files
    """
    # Find the .nc file in the granule directory
    nc_files = [f for f in os.listdir(granule_dir) if f.endswith('.nc')]
    if not nc_files:
        logging.warning(f"No .nc file found in {granule_dir}")
        return
        
    input_file = os.path.join(granule_dir, nc_files[0])
    output_dir = os.path.join(granule_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if TIG has already been run successfully
    success_file = os.path.join(granule_dir, 'tig_successful.txt')
    if os.path.exists(success_file):
        print(f"Skipping TIG processing for {granule_dir} - already completed successfully")
        return
        
    # Run TIG and save output
    tig_output, return_code = run_tig_process(input_file, output_dir, config_file, palette_dir)
    print(f"tig_output: {tig_output}")
    print(f"Return code: {return_code}")
    
    if return_code == 0:
        # Success case - write output to success file
        with open(success_file, 'w') as f:
            f.write(tig_output)
    else:
        # Failure case - create failure file with output
        failed_file = os.path.join(granule_dir, 'tig_failed.txt')
        with open(failed_file, 'w') as f:
            f.write(tig_output)


def main():
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description='Process TIG regression tests')
    parser.add_argument('--workdir', default='workdir', help='Working directory path (default: workdir)')
    args = parser.parse_args()
    
    palette_dir = "../forge-tig-configuration/palettes"  # Update this path as needed
    process_workdir(args.workdir, palette_dir, [process_granule_dir_tig])

if __name__ == "__main__":
    main() 