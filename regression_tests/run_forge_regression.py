import argparse
import logging
import subprocess
import os
import json
from typing import Tuple, Optional
from regression_base import process_workdir

def run_forge_process(input_file: str, config_file: str) -> Tuple[str, int]:
    """
    Run the Forge process on a single granule file and capture output
    
    Args:
        input_file: Path to input granule file
        config_file: Path to config file
        
    Returns:
        Tuple of (output string, return code) from Forge process
    """
    try:
        cmd = [
            'java',
            '-cp', 'footprint.jar',
            'FootprintCLI',
            input_file,
            config_file
        ]
        
        # Print the command being executed
        print("\nExecuting Forge command:")
        print(" ".join(cmd))
        print()
        result = subprocess.run(cmd,
                              capture_output=True,
                              text=True,
                              check=True)
        output = result.stdout + "\n" + result.stderr if result.stderr else result.stdout
        return output, result.returncode
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running Forge command: {e.stderr}")
        output = f"STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        return output, e.returncode


def process_granule_dir_forge(granule_dir: str, config_file: str, palette_dir: Optional[str] = None, output_dir_name: str = 'output') -> None:
    """
    Process a single granule directory for Forge
    
    Args:
        granule_dir: Path to granule directory
        config_file: Path to config file
        palette_dir: Optional palette directory (not used by Forge but needed for function signature compatibility)
    """
    # First check if we should run Forge based on config
    try:
        with open(config_file) as f:
            config = json.load(f)
            if "footprint" not in config or not config["footprint"]:
                print(f"Skipping Forge processing for {granule_dir} - no footprint configuration for this collection")
                # Create skip file indicating why Forge was skipped
                skip_file = os.path.join(granule_dir, 'forge_skip.txt')
                with open(skip_file, 'w') as f:
                    f.write("No footprint configuration for this collection")
                return
            if config.get("footprinter") == "forge-py":
                print(f"Skipping Forge processing for {granule_dir} - config specifies forge-py footprinter")
                # Create skip file indicating why Forge was skipped
                skip_file = os.path.join(granule_dir, 'forge_skip.txt')
                with open(skip_file, 'w') as f:
                    f.write("Config specifies forge-py footprinter")
                return
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Error reading config file {config_file}: {str(e)}")
        return
    # Check if Forge has already been run successfully
    output_dir = os.path.join(granule_dir, output_dir_name)
    os.makedirs(output_dir, exist_ok=True)
    
    forge_success_file = os.path.join(output_dir, 'forge_successful.txt')
    if os.path.exists(forge_success_file):
        print(f"Skipping Forge processing for {granule_dir} - already completed successfully")
        return

    # Find the .nc and .h5 files in the granule directory
    nc_files = [f for f in os.listdir(granule_dir) if f.endswith('.nc') or f.endswith('.h5')]
    if not nc_files:
        logging.warning(f"No .nc or .h5 file found in {granule_dir}")
        return
        
    input_file = os.path.join(granule_dir, nc_files[0])

    # Run Forge and save output
    forge_output, return_code = run_forge_process(input_file, config_file)
    print(f"forge_output: {forge_output}")
    print(f"Return code: {return_code}")
    
    # Find the .wkt file that was created
    wkt_file = None
    for f in os.listdir(granule_dir):
        if f.endswith('.wkt'):
            wkt_file = os.path.join(granule_dir, f)
            break

    if return_code == 0 and "error" not in forge_output.lower():
        # Success case - create success file with output and move wkt file
        with open(forge_success_file, 'w') as f:
            f.write(forge_output)
        if wkt_file:
            os.rename(wkt_file, os.path.join(output_dir, os.path.basename(wkt_file)))
    else:
        # Failure case - create failure file with output and delete wkt file
        failed_file = os.path.join(output_dir, 'forge_failed.txt')
        with open(failed_file, 'w') as f:
            f.write(forge_output)
        if wkt_file:
            os.remove(wkt_file)


def main():
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description='Process Forge regression tests')
    parser.add_argument('--workdir', default='workdir', help='Working directory path (default: workdir)')
    parser.add_argument('--output_dir_name', '-od', required=True, help='Name of output directory for Forge results')
    args = parser.parse_args()

    process_workdir(args.workdir, None, args.output_dir_name, [process_granule_dir_forge])

if __name__ == "__main__":
    main() 