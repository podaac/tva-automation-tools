# UMM-V Related URL Update

`umm_v_update_related_url.py` updates the `RelatedUrls` list for a UMM-V variable in CMR.

It supports three actions:

- add a basic URL entry
- add a full RelatedUrls object from a JSON file
- delete an entry by exact URL match

## Requirements

Set the required authentication environment variables before running the script:

- `LAUNCHPAD_TOKEN`
- `OPS_LAUNCHPAD_TOKEN` for `ops`
- `UAT_LAUNCHPAD_TOKEN` for `uat`

The script uses Launchpad for both CMR lookups and the ingest update.
No EDL token is required.

If you prefer to keep using a single Launchpad token, `LAUNCHPAD_TOKEN` works as a fallback for both environments.

## Basic Usage

```bash
python umm_v_auto/umm_v_update_related_url.py \
  -c COLLECTION_SHORT_NAME \
  -v VARIABLE_NAME \
  -e uat \
  -u https://example.com/data.bin
```

Required flags:

- `-c`, `--collection-name`: collection short name
- `-v`, `--variable-name`: variable name
- `-e`, `--env`: target environment, one of `ops` or `uat`

`-v` is not required (or allowed) when `--filtering-config` is set; see [Filtering Config Mode](#filtering-config-mode).

The `-e` flag controls which CMR venue is queried and which Launchpad token is used:

- `ops` uses `OPS_LAUNCHPAD_TOKEN` if it is set, otherwise `LAUNCHPAD_TOKEN`
- `uat` uses `UAT_LAUNCHPAD_TOKEN` if it is set, otherwise `LAUNCHPAD_TOKEN`

Action flags:

- `-u`, `--new-url`: add a simple URL entry
- `-f`, `--related-url-file`: add a full JSON object from a file
- `-d`, `--delete-url`: delete an entry by exact URL

You must choose exactly one action flag.

## Add a Simple URL

Use `--new-url` when you only need to attach a URL and do not need custom metadata.

The JSON file approach is the preferred option when you need more than a bare URL. The simple URL path fills in default values for the related-url fields, and those defaults may not be the best fit for your use case.

```bash
python umm_v_auto/umm_v_update_related_url.py \
  -c MY_COLLECTION \
  -v MY_VARIABLE \
  -e uat \
  -u https://example.com/data.bin
```

For simple URL adds, the script builds a default RelatedUrls object with:

- `URL`
- `URLContentType`
- `Type`
- `Subtype`
- `Format`
- `MimeType`

## Recommended Way

Use `--related-url-file` whenever possible.

That approach lets you provide the full RelatedUrls object directly, which is better when:

- you need a specific `Type`, `Subtype`, or `URLContentType`
- you want metadata like `Description`, `Format`, or `MimeType`
- the default values from `--new-url` are not appropriate
- you want to add more than one related URL at once

## Add a Full RelatedUrls Object

Use `--related-url-file` when you want to provide the exact object to store in `RelatedUrls`.

Example file, `related_url.json`:

```json
{
  "Description": "Colormap that can be used for this variable in GDAL-compatible text format.",
  "URLContentType": "VisualizationURL",
  "Type": "Color Map",
  "Subtype": "Harmony GDAL",
  "URL": "https://gibs.earthdata.nasa.gov/colormaps/txt/GHRSST_Sea_Surface_Temperature.txt",
  "Format": "Text File",
  "MimeType": "text/plain"
}
```

Run it like this:

```bash
python umm_v_auto/umm_v_update_related_url.py \
  -c MY_COLLECTION \
  -v MY_VARIABLE \
  -e uat \
  -f related_url.json
```

Rules for the JSON file:

- it may contain a single JSON object or a list of JSON objects
- every object must include a non-empty `URL` field
- any other keys are passed through as-is

Example file with multiple entries:

```json
[
  {
    "URL": "https://example.com/one.txt",
    "URLContentType": "VisualizationURL",
    "Type": "Color Map"
  },
  {
    "URL": "https://example.com/two.txt",
    "URLContentType": "VisualizationURL",
    "Type": "Color Map",
    "Description": "Second related URL"
  }
]
```

## Delete a URL

Use `--delete-url` to remove entries whose `URL` matches exactly.

```bash
python umm_v_auto/umm_v_update_related_url.py \
  -c MY_COLLECTION \
  -v MY_VARIABLE \
  -e uat \
  -d https://example.com/data.bin
```

Notes on delete behavior:

- matching is exact
- all entries with that `URL` are removed
- if no match is found, the script exits without updating CMR

## Filtering Config Mode

Add `--filtering-config` to attach (or remove) a filtering rules JSON URL for [harmony-filtering-service](https://github.com/nasa/harmony-filtering-service) on every variable it filters. Use it with `-u` or `-d`, and leave out `-v`.

```bash
python umm_v_auto/umm_v_update_related_url.py \
  --filtering-config \
  -c MY_COLLECTION \
  -e uat \
  -u https://example.com/MY_COLLECTION_filtering.json
```

The script downloads the JSON at the URL and updates each unique `target_var` found in `filters.pixel_filter`. For example, this config updates only `analysed_sst`:

```json
{
  "filters": {
    "pixel_filter": [
      {"target_var": "analysed_sst", "criteria_var": "mask", "operator": "equal-to", "threshold": "2"},
      {"target_var": "analysed_sst", "criteria_var": "sea_ice_fraction", "operator": "greater-than", "threshold": "0"}
    ]
  }
}
```

Each variable gets this RelatedURLs entry:

```json
{
  "URL": "<the -u URL>",
  "URLContentType": "DistributionURL",
  "Type": "SERVICE CONFIGURATION",
  "Subtype": "FILTERING CONFIGURATION",
  "Format": "JSON",
  "MimeType": "application/json"
}
```

Notes:

- `Description` is left out because UMM-Var rejects an empty `Description`
- the config URL must be publicly readable; no token is sent when downloading it
- delete (`-d`) also downloads the config to find the variables, so delete before removing the file from its host
- if one variable fails, the rest are still processed and the script exits with an error at the end

## Uniqueness

RelatedUrls entries need to be unique by `URL`.

If you need to modify an existing entry:

1. delete the existing URL first
2. add the updated entry again

This is the safest way to ensure the updated metadata is stored cleanly.

When adding from a JSON file, duplicate URLs in the file are skipped, and URLs that already exist in the variable are also skipped.

## Defaults And Lookup Behavior

- `--provider` defaults to `POCLOUD`
- collection lookup uses the collection short name and provider
- variable lookup uses the variable name plus the linked collection concept ID
- if multiple variables match, the script stops and reports the candidate concept IDs

## Operational Notes

- The script deduplicates adds by `URL`
- The script updates the UMM payload using the variable's existing record and replaces `RelatedUrls`
- If you are testing in a non-production environment, verify the target `-e` value carefully before running

## Example Workflow

1. Create a JSON file for the new related URL entry if you need custom metadata.
2. Run the script with `--related-url-file` to add it.
3. Run the script with `--delete-url` if you need to remove a bad entry.

## GitHub Actions

There is a manual workflow at `.github/workflows/umm_v_update_related_url.yml` for adding or deleting a single URL.

It accepts these dispatch inputs:

- `collection_name`
- `provider`
- `variable_name`
- `env`
- `action`
- `url`

Set `action` to `add` or `delete`. The workflow fetches the correct Launchpad token for the selected environment and runs the script with `--new-url` or `--delete-url` accordingly.

There is also a manual workflow at `.github/workflows/umm_v_update_filtering_rules.yml` ("Update Filtering Rules"). It takes the same inputs except `variable_name`, and runs the script with `--filtering-config`, so `url` must point to a filtering config JSON.
