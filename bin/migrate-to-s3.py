#!/usr/bin/env python3
"""
Migrate forecasts from local filesystem to S3.

This script copies all forecast files from a local forecasts/ directory
to an S3 bucket, preserving the directory structure.

Usage:
    python3 bin/migrate-to-s3.py --source file://forecasts --dest s3://my-bucket/forecasts
    python3 bin/migrate-to-s3.py --source forecasts --dest s3://my-bucket/forecasts
    python3 bin/migrate-to-s3.py --source file://forecasts --dest s3://my-bucket/forecasts --dry-run
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import fsspec

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_path(path: str) -> str:
    """
    Normalize a path to use file:// protocol if no protocol specified.
    Converts relative paths to absolute paths.

    Args:
        path: Path string (e.g., "forecasts" or "file://forecasts" or "s3://bucket/forecasts")

    Returns:
        Normalized path with protocol
    """
    if '://' not in path:
        # No protocol specified, assume local file
        # Convert to absolute path if relative
        abs_path = os.path.abspath(path)
        return f"file://{abs_path}"
    elif path.startswith('file://'):
        # Already has file:// protocol, ensure path is absolute
        local_path = path[7:]  # Remove 'file://'
        if not os.path.isabs(local_path):
            abs_path = os.path.abspath(local_path)
            return f"file://{abs_path}"
    return path


def get_all_files(fs, base_path: str) -> list:
    """
    Get all JSON files from a filesystem path.

    Args:
        fs: fsspec filesystem instance
        base_path: Base path to search

    Returns:
        List of file paths
    """
    base_normalized = base_path.rstrip('/')

    try:
        # Use glob to find all JSON files recursively
        files = fs.glob(f"{base_normalized}/**/*.json")
        return sorted(files)
    except Exception as e:
        logger.error(f"Error listing files from {base_path}: {e}")
        return []


def migrate_files(source_path: str, dest_path: str, dry_run: bool = False):
    """
    Migrate forecast files from source to destination.

    Args:
        source_path: Source path/URL (e.g., "file://forecasts")
        dest_path: Destination path/URL (e.g., "s3://bucket/forecasts")
        dry_run: If True, only show what would be copied without actually copying
    """
    # Normalize paths
    source_path = normalize_path(source_path)
    dest_path = normalize_path(dest_path)

    logger.info(f"Migration {'simulation' if dry_run else 'started'}")
    logger.info(f"Source: {source_path}")
    logger.info(f"Destination: {dest_path}")

    # Get filesystem instances
    source_fs, _ = fsspec.core.url_to_fs(source_path)
    dest_fs, _ = fsspec.core.url_to_fs(dest_path)

    # Get all source files
    logger.info("Scanning source files...")
    source_files = get_all_files(source_fs, source_path)

    if not source_files:
        logger.warning("No files found in source directory")
        return

    logger.info(f"Found {len(source_files)} files to migrate")

    # Prepare statistics
    stats = {
        'total': len(source_files),
        'copied': 0,
        'skipped': 0,
        'failed': 0
    }

    # Normalize base paths for string manipulation
    source_base = source_path.rstrip('/')
    dest_base = dest_path.rstrip('/')

    # Copy each file
    for source_file in source_files:
        # Calculate relative path
        # fsspec glob may return paths with or without protocol prefix
        # We need to extract the relative path after the base

        # Remove protocol from both paths for comparison
        source_protocol_idx = source_base.find('://')
        if source_protocol_idx >= 0:
            source_base_clean = source_base[source_protocol_idx + 3:]
        else:
            source_base_clean = source_base
        source_base_clean = source_base_clean.rstrip('/')

        file_protocol_idx = source_file.find('://')
        if file_protocol_idx >= 0:
            source_file_clean = source_file[file_protocol_idx + 3:]
        else:
            source_file_clean = source_file

        # Get relative path
        if source_file_clean.startswith(source_base_clean):
            relative_path = source_file_clean[len(source_base_clean):].lstrip('/')
        elif source_file.startswith(source_base):
            # Direct match with protocol
            relative_path = source_file[len(source_base):].lstrip('/')
        else:
            logger.warning(f"Could not determine relative path for {source_file}")
            logger.debug(f"  source_base_clean: {source_base_clean}")
            logger.debug(f"  source_file_clean: {source_file_clean}")
            stats['failed'] += 1
            continue

        dest_file = f"{dest_base}/{relative_path}"

        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would copy: {source_file} -> {dest_file}")
                stats['copied'] += 1
            else:
                # Check if destination file already exists
                if dest_fs.exists(dest_file):
                    logger.debug(f"File already exists, overwriting: {dest_file}")

                # Read from source
                with source_fs.open(source_file, 'rb') as src:
                    data = src.read()

                # Create destination directory if needed
                dest_dir = '/'.join(dest_file.split('/')[:-1])
                dest_fs.makedirs(dest_dir, exist_ok=True)

                # Write to destination
                with dest_fs.open(dest_file, 'wb') as dst:
                    dst.write(data)

                logger.info(f"Copied: {relative_path}")
                stats['copied'] += 1

        except Exception as e:
            logger.error(f"Error copying {source_file}: {e}")
            stats['failed'] += 1

    # Print summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Total files:    {stats['total']}")
    print(f"Copied:         {stats['copied']}")
    print(f"Skipped:        {stats['skipped']}")
    print(f"Failed:         {stats['failed']}")
    print("=" * 60)

    if dry_run:
        print("\nThis was a dry run. No files were actually copied.")
        print(f"Run without --dry-run to perform the actual migration.")
    else:
        print(f"\nMigration complete!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Migrate forecast files from local filesystem to S3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be copied
  %(prog)s --source file://forecasts --dest s3://my-bucket/forecasts --dry-run

  # Actual migration from local to S3
  %(prog)s --source file://forecasts --dest s3://my-bucket/forecasts

  # Can omit file:// for local paths
  %(prog)s --source forecasts --dest s3://my-bucket/forecasts

  # Migrate from one S3 bucket to another
  %(prog)s --source s3://old-bucket/forecasts --dest s3://new-bucket/forecasts

Notes:
  - Existing files at destination will be overwritten
  - Directory structure is preserved
  - Only .json files are migrated
  - For S3, ensure AWS credentials are configured (via environment variables, ~/.aws/credentials, or IAM roles)
        """
    )

    parser.add_argument(
        '--source',
        required=True,
        help='Source path/URL (e.g., "file://forecasts" or "forecasts")'
    )
    parser.add_argument(
        '--dest',
        required=True,
        help='Destination path/URL (e.g., "s3://my-bucket/forecasts")'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be copied without actually copying'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate arguments
    source_normalized = normalize_path(args.source)
    dest_normalized = normalize_path(args.dest)

    if source_normalized == dest_normalized:
        print("Error: Source and destination are the same", file=sys.stderr)
        sys.exit(1)

    # Perform migration
    try:
        migrate_files(args.source, args.dest, dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        logger.exception("Migration error")
        sys.exit(1)


if __name__ == '__main__':
    main()
