#!/usr/bin/env python3
"""
Slotify API Client Script

This script allows users to interact with Slotify's token-protected export and import API endpoints.

Features:
- Reads the API token from a file (default: ~/.slotify_api_token)
- Downloads exported ZIP files from the /api/export endpoint
- Uploads ZIP files to the /api/import endpoint
- Deletes the temporary file after upload
- Supports custom token file, output directory, and base URL

Authentication:
This client uses a Bearer token for API authentication.
You must save your token in a file (default: ~/.slotify_api_token), or use --token-file to specify a custom path.

Usage Examples:
    python slotify_api_client.py export
    python slotify_api_client.py export --output-dir ./backups
    python slotify_api_client.py export --token-file ~/.my_token

    python slotify_api_client.py import ~/Downloads/slotify_export.zip
    python slotify_api_client.py import ~/Downloads/slotify_export.zip --token-file ~/.my_token

    python slotify_api_client.py export --base-url https://slotify.pythonanywhere.com
"""

import argparse
import requests
from pathlib import Path
from scripts.utils import utcnow

# Defaults
DEFAULT_BASE_URL = 'https://slotify.pythonanywhere.com'
DEFAULT_TOKEN_PATH = Path.home() / '.slotify_api_token'
DEFAULT_DOWNLOAD_DIR = Path.home() / 'Downloads'


def load_token(token_path=DEFAULT_TOKEN_PATH):
    """Load the API token from a file."""
    path = Path(token_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Token file not found: {path}")
    
    token = path.read_text().strip()
    if not token:
        raise ValueError("Token file is empty.")
    
    print(f"[✓] Loaded token from {path}")
    return token


def export_data(token, base_url, download_dir=DEFAULT_DOWNLOAD_DIR):
    """Call the API to export data and save it as a ZIP file."""
    print("[→] Initiating export...")
    headers = {'Authorization': f'Bearer {token}'}
    export_endpoint = f'{base_url}/api/export'
    response = requests.get(export_endpoint, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Export failed: {response.status_code} - {response.text}")

    download_dir = Path(download_dir).expanduser()
    download_dir.mkdir(parents=True, exist_ok=True)
    timestamp = utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f'slotify_export_{timestamp}.zip'
    file_path = download_dir / filename

    with open(file_path, 'wb') as f:
        f.write(response.content)

    print(f"[✓] Exported data saved to: {file_path}")
    return file_path


def import_data(token, base_url, zip_file_path):
    """Call the API to import a ZIP file containing database data."""
    file_path = Path(zip_file_path).expanduser()
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    print(f"[→] Initiating import with file: {file_path}")
    headers = {'Authorization': f'Bearer {token}'}
    import_endpoint = f'{base_url}/api/import'

    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'application/zip')}
        response = requests.post(import_endpoint, headers=headers, files=files)

    if response.status_code != 200:
        raise Exception(f"Import failed: {response.status_code} - {response.text}")

    print("[✓] Import successful.")
    return response.json().get('message')


def main():
    parser = argparse.ArgumentParser(description="Slotify API client to export or import data.")
    parser.add_argument('--base-url', type=str, default=DEFAULT_BASE_URL,
                        help=f'Base URL for the API (default: {DEFAULT_BASE_URL})')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Export
    export_parser = subparsers.add_parser('export', help='Export data as ZIP file')
    export_parser.add_argument('--token-file', type=str, default=str(DEFAULT_TOKEN_PATH),
                               help='Path to API token file (default: ~/.slotify_api_token)')
    export_parser.add_argument('--output-dir', type=str, default=str(DEFAULT_DOWNLOAD_DIR),
                               help='Directory to save the exported ZIP (default: ~/Downloads)')

    # Import
    import_parser = subparsers.add_parser('import', help='Import data from a ZIP file')
    import_parser.add_argument('zip_file', type=str, help='Path to ZIP file to upload')
    import_parser.add_argument('--token-file', type=str, default=str(DEFAULT_TOKEN_PATH),
                               help='Path to API token file (default: ~/.slotify_api_token)')

    args = parser.parse_args()

    try:
        token = load_token(args.token_file)

        if args.command == 'export':
            export_data(token, base_url=args.base_url, download_dir=args.output_dir)
        elif args.command == 'import':
            import_data(token, base_url=args.base_url, zip_file_path=args.zip_file)

    except Exception as e:
        print(f"[✗] Error: {e}")


if __name__ == '__main__':
    main()
