import argparse
import logging
import subprocess
import os
import json
from typing import Tuple, Optional
from regression_base import process_workdir

def run_forge_py_process(input_file: str, output_dir: str, config_file: str) -> Tuple[str, int]:
    """
    Run the forge-py process on a single granule file and capture output
    
    Args:
        input_file: Path to input granule file
        output_dir: Directory to store forge-py output
        config_file: Path to config file
        
    Returns:
        Tuple of (output string, return code) from forge-py process
    """
    try:
        output_file = os.path.join(output_dir, 'forge-py-footprint.wkt')
        log_file = os.path.join(output_dir, 'forge-py.log')
        
        cmd = [
            'forge-py',
            '--config', config_file,
            '--granule', input_file,
            '--output_file', output_file,
            '--log-file', log_file,
            '--log-level', 'DEBUG'
        ]
        
        # Print the command being executed
        print("\nExecuting forge-py command:")
        print(f"Input file: {input_file}")
        print(f"Output file: {output_file}")
        print(f"Config file: {config_file}")
        print(f"Log file: {log_file}")
        print(" ".join(cmd))
        print()
        
        result = subprocess.run(cmd,
                              capture_output=True,
                              text=True,
                              check=True)
        output = result.stdout + "\n" + result.stderr if result.stderr else result.stdout
        return output, result.returncode
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running forge-py command: {e.stderr}")
        output = f"STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        return output, e.returncode


def process_granule_dir_forge_py(granule_dir: str, config_file: str, palette_dir: Optional[str] = None, output_dir_name: str = 'output') -> None:
    """
    Process a single granule directory for forge-py
    
    Args:
        granule_dir: Path to granule directory
        config_file: Path to config file
        palette_dir: Directory containing palette files (unused for forge-py)
    """
    # First check if we should run forge-py based on config
    try:
        with open(config_file) as f:
            config = json.load(f)
            if "footprint" not in config or not config["footprint"]:
                print(f"Skipping forge-py processing for {granule_dir} - no footprint configuration for this collection")
                # Create skip file indicating why forge-py was skipped
                skip_file = os.path.join(granule_dir, 'forge-py_skip.txt')
                with open(skip_file, 'w') as f:
                    f.write("No footprint configuration for this collection")
                return
            if config.get("footprinter") != "forge-py":
                print(f"Skipping forge-py processing for {granule_dir} - config specifies another footprinter")
                # Create skip file indicating why forge-py was skipped
                skip_file = os.path.join(granule_dir, 'forge-py_skip.txt')
                with open(skip_file, 'w') as f:
                    f.write("Config specifies another footprinter")
                return
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Error reading config file {config_file}: {str(e)}")
        return

    # Find the .nc and .h5 files in the granule directory
    nc_files = [f for f in os.listdir(granule_dir) if f.endswith('.nc') or f.endswith('.h5')]
    if not nc_files:
        logging.warning(f"No .nc or .h5 file found in {granule_dir}")
        return

    input_file = os.path.join(granule_dir, nc_files[0])
    output_dir = os.path.join(granule_dir, output_dir_name)
    os.makedirs(output_dir, exist_ok=True)

    # Check if forge-py has already been run successfully
    success_file = os.path.join(output_dir, 'forge-py_successful.txt')
    if os.path.exists(success_file):
        print(f"Skipping forge-py processing for {granule_dir} - already completed successfully")
        return

    # Run forge-py and save output
    forge_py_output, return_code = run_forge_py_process(input_file, output_dir, config_file)
    print(f"forge_py_output: {forge_py_output}")
    print(f"Return code: {return_code}")

    if return_code == 0:
        # Success case - write output to success file
        with open(success_file, 'w') as f:
            f.write(forge_py_output)
    else:
        # Failure case - create failure file with output
        failed_file = os.path.join(output_dir, 'forge-py_failed.txt')
        with open(failed_file, 'w') as f:
            f.write(forge_py_output)


def main():
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description='Process forge-py regression tests')
    parser.add_argument('--workdir', default='workdir', help='Working directory path (default: workdir)')
    parser.add_argument('--output_dir_name', '-od', required=True, help='Name of output directory for Forge-py results')
    args = parser.parse_args()

    process_workdir(args.workdir, None, args.output_dir_name, [process_granule_dir_forge_py])

if __name__ == "__main__":
    main() 