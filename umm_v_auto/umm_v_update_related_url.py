"""Script to add, update, or delete a RelatedURLs entry for a UMM-V variable."""

import argparse
import json
import os
import sys
from pathlib import Path
import requests


CMR_URLS = {
    "ops": "https://cmr.earthdata.nasa.gov",
    "uat": "https://cmr.uat.earthdata.nasa.gov",
}


LAUNCHPAD_TOKEN_ENV_VARS = {
    "ops": "OPS_LAUNCHPAD_TOKEN",
    "uat": "UAT_LAUNCHPAD_TOKEN",
}


def get_launchpad_token(env: str) -> str:
    token_env_var = LAUNCHPAD_TOKEN_ENV_VARS.get(env)
    if not token_env_var:
        print(f"ERROR: Unsupported environment '{env}'.", file=sys.stderr)
        sys.exit(1)

    launchpad_token = os.environ.get(token_env_var)
    if launchpad_token:
        return launchpad_token

    fallback_token = os.environ.get("LAUNCHPAD_TOKEN")
    if fallback_token:
        return fallback_token

    print(f"ERROR: {token_env_var} environment variable is not set and LAUNCHPAD_TOKEN fallback is not set.", file=sys.stderr)
    sys.exit(1)


def get_collection_metadata(cmr_base: str, collection_name: str, provider: str, launchpad_token: str) -> dict:
    url = f"{cmr_base}/search/collections.umm_json"
    headers = {"Authorization": launchpad_token}
    params = {"ShortName": collection_name, "provider": provider, "page_size": 2000}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if not items:
        raise ValueError(f"Collection '{collection_name}' not found in CMR ({cmr_base})")
    if len(items) > 1:
        print(f"Warning: {len(items)} collections matched '{collection_name}', using the first result.")
    return items[0]


def get_collection_concept_id(collection_record: dict) -> str:
    return collection_record["meta"]["concept-id"]


def get_variable_candidates(cmr_base: str, variable_name: str, collection_concept_id: str, launchpad_token: str) -> list[dict]:
    url = f"{cmr_base}/search/variables.json"
    headers = {"Authorization": launchpad_token}
    params = {"name": variable_name, "page_size": 2000}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    entries = resp.json().get("items", [])
    return [
        item
        for item in entries
        if collection_concept_id in item.get("associations", {}).get("collections", [])
    ]


def get_variable_record(cmr_base: str, variable_concept_id: str, launchpad_token: str) -> dict:
    url = f"{cmr_base}/search/variables.umm_json"
    headers = {"Authorization": launchpad_token}
    params = {"concept-id": variable_concept_id}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if not items:
        raise ValueError(f"Variable concept ID '{variable_concept_id}' not found in CMR ({cmr_base})")
    return items[0]


def build_new_related_url(new_url: str) -> dict:
    return {
        "URL": new_url,
        "URLContentType": "VisualizationURL",
        "Type": "Color Map",
        "Subtype":"Harmony GDAL",
        "Format":"Text File",
        "MimeType":"text/plain",
        "Description": "Colormap that can be used for this variable in GDAL-compatible text format."
    }


def build_filtering_related_url(new_url: str) -> dict:
    # No "Description" key: UMM-Var requires it to be non-empty when present.
    return {
        "URL": new_url,
        "URLContentType": "DistributionURL",
        "Type": "SERVICE CONFIGURATION",
        "Subtype": "FILTERING CONFIGURATION",
        "Format": "JSON",
        "MimeType": "application/json",
    }


def get_filtering_target_variables(config_url: str) -> list[str]:
    """Download a filtering config JSON and return the unique filters.pixel_filter[].target_var values, in order."""
    resp = requests.get(config_url, timeout=60)
    resp.raise_for_status()
    try:
        config = resp.json()
    except ValueError as exc:
        raise ValueError(f"Filtering config at {config_url} is not valid JSON.") from exc

    pixel_filters = (config.get("filters") or {}).get("pixel_filter") if isinstance(config, dict) else None
    if not isinstance(pixel_filters, list) or not pixel_filters:
        raise ValueError(f"Filtering config at {config_url} has no 'filters.pixel_filter' entries.")

    target_vars = []
    for index, pixel_filter in enumerate(pixel_filters, start=1):
        target_var = pixel_filter.get("target_var") if isinstance(pixel_filter, dict) else None
        if not target_var:
            raise ValueError(f"pixel_filter entry {index} in {config_url} is missing 'target_var'.")
        if target_var not in target_vars:
            target_vars.append(target_var)

    return target_vars


def load_related_url_file(path: str) -> list[dict]:
    file_path = Path(path)
    try:
        with file_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Related URL file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Related URL file is not valid JSON: {path}") from exc

    if isinstance(payload, dict):
        payload = [payload]
    elif not isinstance(payload, list):
        raise ValueError("Related URL file must contain either a JSON object or a list of objects.")

    if not payload:
        raise ValueError("Related URL file must not be empty.")

    for index, entry in enumerate(payload, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Related URL file entry {index} must be a JSON object.")
        if not entry.get("URL"):
            raise ValueError(f"Related URL file entry {index} must include a non-empty 'URL' field.")

    return payload


def update_variable(cmr_base: str, collection_concept_id: str, native_id: str, umm: dict, launchpad_token: str) -> dict:
    url = f"{cmr_base}/ingest/collections/{collection_concept_id}/variables/{native_id}"
    headers = {
        "Content-Type": "application/vnd.nasa.cmr.umm+json",
        "Authorization": launchpad_token,
        "Accept": "application/json",
    }
    resp = requests.put(url, data=json.dumps(umm, allow_nan=False), headers=headers)
    if not resp.ok:
        # CMR puts the reason for a rejected update in the response body, so include it in the error.
        try:
            details = "\n\t".join(str(error) for error in resp.json().get("errors", [])) or resp.text
        except ValueError:
            details = resp.text
        raise RuntimeError(f"CMR ingest returned {resp.status_code} for {url}:\n\t{details}")
    return resp.json()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Add a new URL to the RelatedURLs of a UMM-V variable.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c", "--collection-name",
        required=True,
        metavar="COLLECTION_NAME",
        help="Short name of the collection (e.g. SMAP_RSS_L3_SSS_SMI_8DAY_V4)",
    )
    parser.add_argument(
        "-v", "--variable-name",
        required=False,
        metavar="VARIABLE_NAME",
        help="Name of the UMM-V variable to update (required unless --filtering-config is set)",
    )
    parser.add_argument(
        "--filtering-config",
        action="store_true",
        help=(
            "Treat the --new-url/--delete-url value as a filtering config JSON. The variables to update are "
            "read from its filters.pixel_filter[].target_var values, and added entries use the filtering "
            "RelatedURLs metadata."
        ),
    )
    parser.add_argument(
        "-u", "--new-url",
        required=False,
        metavar="NEW_URL",
        help="New URL to add to the variable's RelatedURLs",
    )
    parser.add_argument(
        "-f", "--related-url-file",
        required=False,
        metavar="FILE",
        help="Path to a JSON file containing a full RelatedURLs entry to add",
    )
    parser.add_argument(
        "-d", "--delete-url",
        required=False,
        metavar="URL",
        help="Exact URL to remove from the variable's RelatedURLs",
    )
    parser.add_argument(
        "-e", "--env",
        required=True,
        choices=["ops", "uat"],
        help="CMR environment to target",
    )
    parser.add_argument(
        "-p", "--provider",
        default="POCLOUD",
        metavar="PROVIDER",
        help="CMR provider to target for the collection lookup",
    )
    args = parser.parse_args()

    action_count = sum(
        1 for value in [args.new_url, args.related_url_file, args.delete_url] if value
    )
    if action_count != 1:
        parser.error("Specify exactly one of --new-url, --related-url-file, or --delete-url.")

    if args.filtering_config:
        if args.variable_name:
            parser.error("--variable-name cannot be used with --filtering-config; variables come from the config.")
        if args.related_url_file:
            parser.error("--filtering-config requires --new-url or --delete-url, not --related-url-file.")
    elif not args.variable_name:
        parser.error("--variable-name is required unless --filtering-config is set.")

    return args


def update_variable_related_urls(
    cmr_base: str,
    collection_concept_id: str,
    variable_name: str,
    *,
    new_entries: list[dict] | None,
    delete_url: str | None,
    launchpad_token: str,
) -> bool:
    """Add or delete RelatedURLs entries for one variable. Returns True if CMR was updated."""
    print(f"Searching for variable keyword '{variable_name}'...")
    variable_candidates = get_variable_candidates(cmr_base, variable_name, collection_concept_id, launchpad_token)
    if not variable_candidates:
        raise ValueError(
            f"No variable found for keyword '{variable_name}' linked to collection '{collection_concept_id}' "
            f"in CMR ({cmr_base})"
        )

    if len(variable_candidates) > 1:
        candidate_ids = ", ".join(item.get("concept_id", "<unknown>") for item in variable_candidates)
        raise ValueError(
            f"Multiple variables matched keyword '{variable_name}' and collection '{collection_concept_id}'. "
            f"Candidate variable concept IDs: {candidate_ids}"
        )

    variable_concept_id = variable_candidates[0]["concept_id"]
    print(f"Found linked variable concept ID: {variable_concept_id}")

    variable_record = get_variable_record(cmr_base, variable_concept_id, launchpad_token)
    meta = variable_record["meta"]
    umm = variable_record["umm"]
    native_id = meta["native-id"]
    concept_id = meta["concept-id"]
    print(f"Found variable: {concept_id} (native-id: {native_id})")

    existing_urls = umm.get("RelatedURLs", [])

    if delete_url:
        filtered_urls = [entry for entry in existing_urls if entry.get("URL") != delete_url]
        if len(filtered_urls) == len(existing_urls):
            print(f"URL not found in RelatedURLs for variable '{variable_name}'. No update needed.")
            return False
        updated_umm = {**umm, "RelatedURLs": filtered_urls}
        if not filtered_urls:
            # UMM-Var rejects an empty RelatedURLs list, so drop the field instead.
            del updated_umm["RelatedURLs"]
        print(f"Updating variable by deleting URL: {delete_url}")
    else:
        existing_url_values = {entry.get("URL") for entry in existing_urls}
        seen_input_urls = set()
        entries_to_add = []

        for new_entry in new_entries:
            new_url = new_entry["URL"]
            if new_url in existing_url_values:
                print(f"URL already exists in RelatedURLs for variable '{variable_name}': {new_url}. Skipping.")
                continue
            if new_url in seen_input_urls:
                print(f"Duplicate URL in input file skipped: {new_url}")
                continue
            seen_input_urls.add(new_url)
            entries_to_add.append(new_entry)

        if not entries_to_add:
            print(f"No new URLs to add for variable '{variable_name}'. No update needed.")
            return False

        updated_umm = {**umm, "RelatedURLs": existing_urls + entries_to_add}
        print(
            "Updating variable with new URL(s): "
            + ", ".join(entry["URL"] for entry in entries_to_add)
        )

    response = update_variable(cmr_base, collection_concept_id, native_id, updated_umm, launchpad_token)

    if "errors" in response:
        raise RuntimeError("CMR ingest failed:\n\t" + "\n\t".join(response["errors"]))

    print(f"SUCCESS: Variable '{variable_name}' updated. Concept ID: {response.get('concept-id')}")
    return True


def main():
    args = parse_args()

    launchpad_token = get_launchpad_token(args.env)

    cmr_base = CMR_URLS[args.env]
    provider = args.provider.upper()

    if args.filtering_config:
        config_url = args.new_url or args.delete_url
        print(f"Reading filtering config from {config_url}...")
        variable_names = get_filtering_target_variables(config_url)
        print(f"Variables to update from filtering config: {', '.join(variable_names)}")
    else:
        variable_names = [args.variable_name]

    new_entries = None
    if args.related_url_file:
        new_entries = load_related_url_file(args.related_url_file)
    elif args.new_url:
        if args.filtering_config:
            new_entries = [build_filtering_related_url(args.new_url)]
        else:
            new_entries = [build_new_related_url(args.new_url)]

    print(f"Looking up collection '{args.collection_name}' for provider '{provider}' in {args.env} ({cmr_base})...")
    collection_record = get_collection_metadata(cmr_base, args.collection_name, provider, launchpad_token)
    collection_concept_id = get_collection_concept_id(collection_record)
    print(f"Found collection concept ID: {collection_concept_id}")

    failed = []
    for variable_name in variable_names:
        try:
            update_variable_related_urls(
                cmr_base,
                collection_concept_id,
                variable_name,
                new_entries=new_entries,
                delete_url=args.delete_url,
                launchpad_token=launchpad_token,
            )
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            print(f"ERROR: Failed to update variable '{variable_name}': {exc}", file=sys.stderr)
            failed.append(variable_name)

    if failed:
        print(f"ERROR: {len(failed)} of {len(variable_names)} variable(s) failed: {', '.join(failed)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
