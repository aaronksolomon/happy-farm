#!/usr/bin/env python3
"""
Quick script to import .gdoc files from Google Drive to markdown.

.gdoc files are just JSON pointers - this script reads the doc ID and uses
Google Drive API to download as .docx, then converts to markdown with pandoc.
"""

import json
import subprocess
from pathlib import Path
import click


def read_gdoc_id(gdoc_path: Path) -> str:
    """Extract document ID from .gdoc file."""
    with open(gdoc_path, 'r') as f:
        data = json.load(f)
    return data.get('doc_id') or data.get('url', '').split('/')[-2]


def download_via_browser(doc_id: str, output_path: Path):
    """
    Downloads a Google Doc by opening browser download URL.
    User must be logged into Google in their default browser.
    """
    download_url = f"https://docs.google.com/document/d/{doc_id}/export?format=docx"
    click.echo(f"Opening browser to download document...")
    click.echo(f"URL: {download_url}")
    click.echo(f"Save to: {output_path}")
    subprocess.run(['open', download_url])
    click.echo("\nAfter download completes, move the .docx file to the path above.")


def convert_docx_to_md(docx_path: Path, md_path: Path) -> bool:
    """Convert DOCX to Markdown using Pandoc."""
    try:
        subprocess.run(
            ["pandoc", str(docx_path), "-o", str(md_path), "--wrap=none"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        click.echo(f"Error converting to markdown: {e}", err=True)
        return False


@click.command()
@click.option('--gdrive-path',
              type=click.Path(exists=True),
              help='Path to Google Drive shared folder (e.g., ~/Library/CloudStorage/.../happy-farm-data)')
@click.option('--output-dir',
              type=click.Path(),
              default='docs/farm-resources',
              help='Output directory for markdown files')
@click.option('--docx-dir',
              type=click.Path(),
              default='docs/farm-resources/tmp-docx',
              help='Temporary directory for .docx files')
def import_docs(gdrive_path: str, output_dir: str, docx_dir: str):
    """
    Import Google Docs (.gdoc) to markdown.

    This is a MANUAL process:
    1. Script lists all .gdoc files
    2. For each, you manually download the .docx from browser
    3. Script converts .docx to .md

    For automated sync, we'd need Google Drive API setup.
    """
    gdrive = Path(gdrive_path)
    output = Path(output_dir)
    docx_tmp = Path(docx_dir)

    output.mkdir(parents=True, exist_ok=True)
    docx_tmp.mkdir(parents=True, exist_ok=True)

    # Find all .gdoc files
    gdoc_files = list(gdrive.glob('*.gdoc'))

    if not gdoc_files:
        click.echo("No .gdoc files found in the specified directory")
        return

    click.echo(f"Found {len(gdoc_files)} Google Doc files:\n")

    for gdoc in gdoc_files:
        doc_name = gdoc.stem
        click.echo(f"\n{'='*60}")
        click.echo(f"Document: {doc_name}")
        click.echo(f"{'='*60}")

        # Read doc ID
        try:
            with open(gdoc, 'r') as f:
                data = json.load(f)
            doc_id = data.get('doc_id', '')
            url = data.get('url', '')

            if not doc_id and url:
                # Try to extract from URL
                doc_id = url.split('/d/')[-1].split('/')[0]

            if not doc_id:
                click.echo(f"⚠️  Could not find doc ID in {gdoc}")
                continue

        except Exception as e:
            click.echo(f"⚠️  Error reading {gdoc}: {e}")
            continue

        # Paths
        docx_path = docx_tmp / f"{doc_name}.docx"
        md_path = output / f"{doc_name}.md"

        # Download instructions
        download_url = f"https://docs.google.com/document/d/{doc_id}/export?format=docx"

        click.echo(f"\n1. Download URL (opening in browser now):")
        click.echo(f"   {download_url}")
        click.echo(f"\n2. Save downloaded file as:")
        click.echo(f"   {docx_path}")

        # Open in browser
        subprocess.run(['open', download_url], check=False)

        # Wait for user
        click.echo("\n3. Press Enter after you've saved the .docx file (or 's' to skip)...")
        response = input().strip().lower()

        if response == 's':
            click.echo("Skipped.")
            continue

        # Convert if docx exists
        if docx_path.exists():
            click.echo(f"\n4. Converting to markdown...")
            if convert_docx_to_md(docx_path, md_path):
                click.echo(f"✅ Created: {md_path}")
            else:
                click.echo(f"❌ Failed to convert")
        else:
            click.echo(f"⚠️  .docx file not found at {docx_path}")

    click.echo(f"\n{'='*60}")
    click.echo("Import complete!")
    click.echo(f"\nMarkdown files in: {output}")
    click.echo(f"DOCX files in: {docx_tmp}")


if __name__ == '__main__':
    import_docs()
