import json
import os
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class BrowseImageResult:
    fileName: str
    checksum: str
    checksumType: str
    variable: str
    output_crs: str
    dataday: str

    @property
    def key(self) -> str:
        return f"{self.variable}|{self.output_crs}|{self.dataday}|{self.fileName}"


@dataclass
class CnmResults:
    short_name: str
    granule_ur: str
    cmr_env: str
    cnm_file_count: int = 0
    browse_images: list[BrowseImageResult] = field(default_factory=list)


def load_cnm_files(short_name: str, granule_ur: str, cmr_env: str, cnm_dir: str) -> CnmResults:
    results = CnmResults(short_name=short_name, granule_ur=granule_ur, cmr_env=cmr_env)

    if not os.path.isdir(cnm_dir):
        return results

    for filename in sorted(os.listdir(cnm_dir)):
        if not filename.endswith('.json'):
            continue

        results.cnm_file_count += 1

        filepath = os.path.join(cnm_dir, filename)
        with open(filepath, 'r') as f:
            cnm_data = json.load(f)

        for pf in cnm_data.get('product', {}).get('files', []):
            if pf.get('type') == 'browse':
                results.browse_images.append(BrowseImageResult(
                    fileName=pf.get('fileName', ''),
                    checksum=pf.get('checksum', ''),
                    checksumType=pf.get('checksumType', ''),
                    variable=pf.get('variable', ''),
                    output_crs=pf.get('output_crs', ''),
                    dataday=pf.get('dataday', ''),
                ))

    return results


def compare(reference: CnmResults, current: CnmResults) -> str:
    if reference.cnm_file_count == 0:
        return "MISMATCH\nNo reference data found for comparison"

    issues = []

    if reference.short_name != current.short_name:
        issues.append(f"short_name mismatch: reference={reference.short_name}, current={current.short_name}")
    if reference.granule_ur != current.granule_ur:
        issues.append(f"granule_ur mismatch: reference={reference.granule_ur}, current={current.granule_ur}")
    if reference.cmr_env != current.cmr_env:
        issues.append(f"cmr_env mismatch: reference={reference.cmr_env}, current={current.cmr_env}")

    if reference.cnm_file_count != current.cnm_file_count:
        issues.append(f"CNM file count: reference={reference.cnm_file_count}, current={current.cnm_file_count}")

    ref_keys = [img.key for img in reference.browse_images]
    cur_keys = [img.key for img in current.browse_images]

    for k, n in Counter(ref_keys).items():
        if n > 1:
            issues.append(f"Duplicate in reference: {k}")
    for k, n in Counter(cur_keys).items():
        if n > 1:
            issues.append(f"Duplicate in current: {k}")

    ref_set = set(ref_keys)
    cur_set = set(cur_keys)

    only_in_reference = ref_set - cur_set
    only_in_current = cur_set - ref_set

    ref_map = {img.key: img for img in reference.browse_images}
    cur_map = {img.key: img for img in current.browse_images}

    for key in only_in_reference:
        img = ref_map[key]
        issues.append(f"Missing from current: {img.fileName} [{img.variable}]")

    for key in only_in_current:
        img = cur_map[key]
        issues.append(f"Extra in current: {img.fileName} [{img.variable}]")

    for key in ref_set & cur_set:
        if ref_map[key].checksumType != cur_map[key].checksumType:
            issues.append(f"ChecksumType mismatch: {ref_map[key].fileName} [{ref_map[key].variable}]")
        if ref_map[key].checksum != cur_map[key].checksum:
            issues.append(f"Checksum mismatch: {ref_map[key].fileName} [{ref_map[key].variable}]")

    if not issues:
        return "MATCH"

    return "MISMATCH\n" + "\n".join(issues)
