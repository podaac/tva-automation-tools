"""
Copy workdir results into reference_data as the golden baseline for future comparisons.

Copies workdir/<short_name>/ into reference_data/<short_name>/, excluding the
'files' directory (browse images are not stored in reference). Then flattens the
cmr_env subdirectory so the final structure is:

    reference_data/<short_name>/<granuleUR>/cnm/*.json

Usage:
    poetry run python load_ref_data.py collections.txt
    poetry run python load_ref_data.py --cmr-env OPS collections.txt
"""

import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='Text file with one short_name per line')
    parser.add_argument('--cmr-env', choices=['UAT', 'OPS'], default='UAT')
    args = parser.parse_args()

    short_names = [line.strip() for line in Path(args.input_file).read_text().splitlines() if line.strip()]

    copied = 0
    for short_name in short_names:
        short_name_path = Path(short_name)
        if short_name_path.is_absolute() or ".." in short_name_path.parts or short_name_path.name != short_name:
            print(f"SKIP: invalid short_name {short_name!r}")
            continue

        src = Path("workdir") / short_name
        dst = Path("reference_data") / short_name
        if not src.exists():
            print(f"SKIP: {src} does not exist")
            continue

        if dst.exists():
            shutil.rmtree(dst)

        print(f"Copying: {src} -> {dst}")
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('files'))

        # Move contents from <granuleUR>/UAT/ up to <granuleUR>/
        for granule_dir in dst.iterdir():
            env_dir = granule_dir / args.cmr_env
            if env_dir.is_dir():
                for item in env_dir.iterdir():
                    shutil.move(str(item), str(granule_dir / item.name))
                env_dir.rmdir()

        copied += 1

    print(f"\nDone: {copied}/{len(short_names)} collections copied")


if __name__ == "__main__":
    main()
