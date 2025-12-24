# Future Enhancements

This document outlines planned future enhancements to AvyRss.

## Planned Enhancements

### 1. Expanded HTML Content for RSS Feed Entries

**Status**: Not yet implemented

**Goal**: Include more forecast information in RSS feed entries beyond just the bottom-line summary.

**Details**:
- Add danger ratings with visual indicators
- Include forecast confidence levels
- Add weather summary
- Include avalanche problem types
- Optionally embed forecast images/graphics

**Benefits**:
- More useful RSS feeds without clicking through
- Better at-a-glance information
- Still maintains link to full forecast

**Implementation Considerations**:
- Keep HTML simple and standards-compliant
- Test in multiple RSS readers
- Don't make feeds too large (balance detail vs size)
- Ensure content displays well across different RSS reader applications

### 2. Move Storage to S3

**Status**: Not yet implemented

**Goal**: Store forecasts and feeds in S3 instead of local filesystem.

**Benefits**:
- Scalable storage
- Better for multi-server deployments
- Simpler backups and archival
- Can use CloudFront CDN for feeds

**Implementation Plan**:
- Use boto3 for S3 operations
- Maintain same logical directory structure in S3
- Keep filesystem as fallback option for local development
- Update both offline (manage.py) and online (Flask) code
- Environment variables for S3 bucket configuration

**Considerations**:
- Cost of S3 storage and requests
- Latency impact (should be minimal for static files)
- Local development workflow (can still use filesystem)
- Migration path for existing data

## Prioritization

Current focus:
1. **Stability**: Ensure reliable daily updates
2. **Content quality**: Implement enhancement #1 (better RSS content)
3. **Scalability**: Implement enhancement #2 (S3 storage)
4. **Documentation**: Keep docs up to date
5. **Bug fixes**: Address any issues that arise
