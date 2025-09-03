# VidTanium User Guide

Complete guide to all VidTanium features and capabilities.

## Table of Contents

1. [Interface Overview](#interface-overview)
2. [Download Management](#download-management)
3. [Settings & Configuration](#settings--configuration)
4. [Advanced Features](#advanced-features)
5. [Troubleshooting](#troubleshooting)

## Interface Overview

### Dashboard

The Dashboard provides an at-a-glance view of your download activities:

- **Statistics**: Total tasks, running downloads, completion rates
- **Quick Actions**: Fast access to common operations
- **System Status**: Performance metrics and health indicators
- **Recent Activity**: Latest download tasks and their status

### Download Manager

The Download Manager is your control center for all download operations:

- **Task Queue**: View and manage all download tasks
- **Progress Monitoring**: Real-time progress for active downloads
- **Batch Operations**: Control multiple downloads simultaneously
- **Task Details**: Detailed information for each download

### Activity Logs

Monitor all application activities:

- **Real-time Logging**: Live view of all operations
- **Filtering**: Filter logs by type, date, or keyword
- **Export**: Save logs for troubleshooting
- **Search**: Find specific events quickly

## Download Management

### Adding Downloads

#### Single URL Download

1. Navigate to Dashboard or Download Manager
2. Enter the video URL in the input field
3. (Optional) Click the folder icon to choose custom output directory
4. Click "Add Task" to begin download

#### Batch URL Import

1. Click "Batch Import" button
2. Choose input method:
   - **Paste URLs**: Enter multiple URLs, one per line
   - **Import File**: Load URLs from a text file
3. Configure batch settings:
   - Output directory
   - Naming pattern
   - Concurrent downloads limit
4. Click "Import All"

### Managing Download Tasks

#### Task Controls

- **Play/Pause**: Start or pause individual downloads
- **Stop**: Cancel and remove download task
- **Retry**: Restart failed downloads
- **Priority**: Move tasks up/down in queue

#### Bulk Operations

Select multiple tasks to:
- Start/pause all selected
- Cancel multiple downloads
- Change output directory
- Export task list

### Download Options

#### Quality Settings

- **Auto**: Automatically select best available quality
- **Custom**: Choose specific resolution/bitrate
- **Multiple**: Download multiple quality versions

#### Output Settings

- **Directory**: Choose where files are saved
- **Naming**: Customize file naming patterns
- **Format**: Select output format (when conversion is available)

## Settings & Configuration

### General Settings

- **Language**: Choose interface language
- **Theme**: Select light or dark theme
- **Startup**: Configure application startup behavior
- **Updates**: Enable/disable automatic update checks

### Download Settings

#### Performance

- **Concurrent Downloads**: Maximum simultaneous downloads
- **Thread Count**: Threads per download (for M3U8)
- **Retry Attempts**: Number of retry attempts for failed segments
- **Timeout**: Network timeout settings

#### Network

- **Proxy Settings**: Configure proxy server if needed
- **User Agent**: Custom user agent string
- **Headers**: Additional HTTP headers
- **Rate Limiting**: Bandwidth throttling options

#### Storage

- **Default Directory**: Default download location
- **Temporary Files**: Temporary file handling
- **Cleanup**: Automatic cleanup of incomplete downloads
- **Disk Space**: Minimum free space requirements

### Advanced Settings

- **Logging Level**: Control log verbosity
- **Debug Mode**: Enable detailed debugging
- **Performance Monitoring**: System resource monitoring
- **Experimental Features**: Beta feature toggles

## Advanced Features

### Scheduled Downloads

Set up automatic downloads:

1. Open Schedule Manager
2. Create new schedule
3. Configure:
   - URLs or URL patterns
   - Download time/frequency
   - Output settings
4. Enable schedule

### Media Processing

Post-download processing options:

- **Format Conversion**: Convert to different formats
- **Quality Adjustment**: Modify resolution/bitrate
- **Metadata Editing**: Add/modify file metadata
- **Batch Processing**: Process multiple files

### Automation

- **Watch Folders**: Monitor folders for new URL files
- **API Integration**: REST API for external control
- **Command Line**: CLI interface for scripting
- **Webhooks**: Notifications to external services

## Performance Optimization

### Network Optimization

- Use wired connection for stability
- Configure appropriate concurrent download limits
- Adjust thread count based on content type
- Enable bandwidth monitoring

### System Optimization

- Ensure sufficient RAM for large downloads
- Use SSD storage for better performance
- Close unnecessary applications
- Monitor CPU and memory usage

### Troubleshooting Performance

- Check network speed and stability
- Verify sufficient disk space
- Monitor system resources
- Review error logs for bottlenecks

## Best Practices

### Download Management

- Organize downloads into folders
- Use descriptive naming patterns
- Regular cleanup of completed downloads
- Monitor disk space usage

### Security

- Verify URLs before downloading
- Use trusted proxy servers only
- Keep application updated
- Review downloaded content

### Maintenance

- Regular log cleanup
- Update application regularly
- Backup important settings
- Monitor system performance

---

For specific issues, see [Troubleshooting](troubleshooting.md) or check the Activity Logs for detailed error information.
