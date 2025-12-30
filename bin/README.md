# Utility Scripts

This directory contains utility scripts for managing AvyRSS.

## Scripts

### `manage.py`

Main CLI tool for offline operations.

**Usage:**
```bash
# Full update (download forecasts + generate feeds)
python3 bin/manage.py full-update

# Download single forecast
python3 bin/manage.py download-forecast <center-slug> <zone-slug>

# Generate single feed
python3 bin/manage.py generate-feed <center-slug> <zone-slug>

# Generate all feeds (without downloading new forecasts)
python3 bin/manage.py generate-all-feeds

# Generate index page
python3 bin/manage.py generate-index

# Help
python3 bin/manage.py --help
```

### `update-feeds.sh`

Automated update script for production deployments. This script:
1. Clones the repository (if not exists) or pulls latest changes
2. Activates the Python virtual environment
3. Downloads latest forecasts
4. Generates updated RSS feeds

**Usage:**
```bash
./bin/update-feeds.sh <base_directory>
```

**Example:**
```bash
# Update in /var/www/avyrss
./bin/update-feeds.sh /var/www

# Update in home directory
./bin/update-feeds.sh ~/apps
```

**Configuration:**

The script uses the `AVYRSS_REPO_URL` environment variable for the repository URL.

**Default repository:** `https://github.com/MarkRoddy/avyrss.git`

To use a different repository, set the environment variable:

```bash
export AVYRSS_REPO_URL="https://github.com/yourfork/avyrss.git"
./bin/update-feeds.sh /var/www
```

Or edit the `REPO_URL` variable in the script directly.

**Cron Setup:**

To run daily at 6 AM:

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths as needed)
0 6 * * * /path/to/avyrss/bin/update-feeds.sh /var/www >> /var/log/avyrss-update.log 2>&1
```

### `migrate-to-s3.py`

Migration tool to copy forecast files from local filesystem to S3 (or between any fsspec-supported storage backends).

**Usage:**
```bash
# Dry run to see what would be copied
python3 bin/migrate-to-s3.py --source forecasts --dest s3://my-bucket/forecasts --dry-run

# Actual migration from local to S3
python3 bin/migrate-to-s3.py --source forecasts --dest s3://my-bucket/forecasts

# Can use explicit file:// protocol
python3 bin/migrate-to-s3.py --source file://forecasts --dest s3://my-bucket/forecasts

# Migrate between S3 buckets
python3 bin/migrate-to-s3.py --source s3://old-bucket/forecasts --dest s3://new-bucket/forecasts

# Verbose output
python3 bin/migrate-to-s3.py --source forecasts --dest s3://my-bucket/forecasts --verbose
```

**Features:**
- Preserves directory structure
- Only migrates `.json` files
- Overwrites existing files at destination
- Supports dry-run mode to preview operations
- Works with any fsspec-supported backend (local, S3, GCS, Azure, etc.)

**AWS Configuration:**
When migrating to/from S3, ensure AWS credentials are configured:
- Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`
- AWS CLI configuration: `~/.aws/credentials`
- IAM roles (if running on EC2/ECS)

### `generate_centers_config.py`

One-time script to generate the `avalanche_centers.yaml` configuration file.

**Usage:**
```bash
python3 bin/generate_centers_config.py
```

**Note:** This file should already exist in the repository. Only run this if the file is missing or you need to regenerate it.

## Script Permissions

All scripts should be executable:

```bash
chmod +x bin/*.sh
chmod +x bin/*.py
```

## Error Handling

All scripts:
- Exit with non-zero status on failure
- Log errors to stderr
- Provide helpful error messages
- Can be safely run via cron

## Logging

For production cron jobs, redirect output to a log file:

```bash
# Example cron entry with logging
0 6 * * * /path/to/bin/update-feeds.sh /var/www >> /var/log/avyrss-update.log 2>&1
```

Or use a separate log file for errors:

```bash
# Separate logs for stdout and stderr
0 6 * * * /path/to/bin/update-feeds.sh /var/www >> /var/log/avyrss-update.log 2>> /var/log/avyrss-error.log
```
