import os
import subprocess
import logging
import argparse
import json

def run_forge_process(input_file: str, config_file: str) -> tuple[str, int]:
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
            '-cp', 'footprint_0.12.0.jar',
            'FootprintCLI',
            input_file,
            config_file
        ]
        
        # Print the command being executed
        print("\nExecuting Forge command:")
        print(f"Input file: {input_file}")
        print(f"Config file: {config_file}")
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


def run_tig_process(input_file: str, output_dir: str, config_file: str, palette_dir: str) -> tuple[str, int]:
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


def process_granule_dir(granule_dir: str, config_file: str, palette_dir: str) -> None:
    """
    Process a single granule directory
    
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
    else:
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

    # Check if we should run forge based on config and previous runs
    run_forge = True
    forge_success_file = os.path.join(granule_dir, 'forge_successful.txt')
    if os.path.exists(forge_success_file):
        print(f"Skipping Forge processing for {granule_dir} - already completed successfully")
        run_forge = False
    else:
        try:
            with open(config_file) as f:
                config = json.load(f)
                if "footprint" not in config or not config["footprint"]:
                    run_forge = False
                    print(f"Skipping Forge processing for {granule_dir} - no footprint configuration for this collection")
                elif config.get("footprinter") == "forge-py":
                    run_forge = False
                    print(f"Skipping Forge processing for {granule_dir} - config specifies forge-py footprinter")
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Error reading config file {config_file} - proceeding with default forge processing")

    if run_forge:
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

        if "Error" not in forge_output:
            # Success case - create success file with output and move wkt file
            success_file = os.path.join(granule_dir, 'forge_successful.txt')
            with open(success_file, 'w') as f:
                f.write(forge_output)
            if wkt_file:
                os.rename(wkt_file, os.path.join(output_dir, os.path.basename(wkt_file)))
        else:
            # Failure case - create failure file with output and delete wkt file
            failed_file = os.path.join(granule_dir, 'forge_failed.txt')
            with open(failed_file, 'w') as f:
                f.write(forge_output)
            if wkt_file:
                os.remove(wkt_file)



def process_collection_dir(collection_dir: str, palette_dir: str) -> None:
    """
    Process a single collection directory
    
    Args:
        collection_dir: Path to collection directory
        palette_dir: Directory containing palette files
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
            process_granule_dir(item_path, config_file, palette_dir)
            print()


def process_workdir(workdir: str, palette_dir: str) -> None:
    """
    Process the entire workdir containing collection directories
    
    Args:
        workdir: Path to working directory
        palette_dir: Directory containing palette files
    """
    if not os.path.exists(workdir):
        logging.error(f"Working directory {workdir} does not exist")
        return

    # Process each collection directory
    # Sort directories alphabetically
    for item in sorted(os.listdir(workdir)):
        collection_dir = os.path.join(workdir, item)
        if os.path.isdir(collection_dir):
            process_collection_dir(collection_dir, palette_dir)


def main():
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description='Process TIG regression tests')
    parser.add_argument('--workdir', default='workdir', help='Working directory path (default: workdir)')
    args = parser.parse_args()
    
    palette_dir = "../forge-tig-configuration/palettes"  # Update this path as needed
    process_workdir(args.workdir, palette_dir)

if __name__ == "__main__":
    main()
