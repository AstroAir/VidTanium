# VidTanium User Manual

## Table of Contents

1. [Getting Started](#getting-started)
2. [Interface Overview](#interface-overview)
3. [Downloading Videos](#downloading-videos)
4. [Managing Downloads](#managing-downloads)
5. [Media Processing](#media-processing)
6. [Settings & Configuration](#settings--configuration)
7. [Troubleshooting](#troubleshooting)
8. [Tips & Best Practices](#tips--best-practices)

## Getting Started

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.14+, or Linux
- **Python**: Version 3.11 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 2GB free space for installation and temporary files
- **Network**: Stable internet connection for downloads

### Installation

#### Windows

1. **Download the installer** from the official website
2. **Run the installer** and follow the setup wizard
3. **Launch VidTanium** from the desktop shortcut or Start menu

#### macOS

1. **Download the DMG file** from the official website
2. **Open the DMG** and drag VidTanium to Applications folder
3. **Launch VidTanium** from Applications or Launchpad

#### Linux

1. **Download the AppImage** from the official website
2. **Make it executable**: `chmod +x VidTanium.AppImage`
3. **Run VidTanium**: `./VidTanium.AppImage`

#### From Source

1. **Install Python 3.11+** and Git
2. **Clone the repository**:

   ```bash
   git clone https://github.com/your-org/vidtanium.git
   cd vidtanium
   ```

3. **Install dependencies**:

   ```bash
   pip install -e .
   ```

4. **Run the application**:

   ```bash
   python main.py
   ```

### First Launch

When you first launch VidTanium:

1. **Welcome Screen**: You'll see a welcome message with quick setup options
2. **Settings Check**: The application will verify your configuration
3. **FFmpeg Detection**: VidTanium will check for FFmpeg installation
4. **Theme Selection**: Choose your preferred theme (Light/Dark/Auto)

## Interface Overview

### Main Window Layout

VidTanium features a modern, intuitive interface with four main sections:

```
┌─────────────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help                 [_][□][X] │
├─────────────────────────────────────────────────────────┤
│ ┌─────────┐ │                                           │
│ │Dashboard│ │           Main Content Area               │
│ │Download │ │                                           │
│ │Logs     │ │                                           │
│ │Settings │ │                                           │
│ └─────────┘ │                                           │
└─────────────────────────────────────────────────────────┘
```

#### Navigation Sidebar

- **Dashboard**: Overview of download statistics and quick actions
- **Download Manager**: Manage active and completed download tasks
- **Activity Logs**: View detailed application logs and events
- **Settings**: Configure application preferences and options

#### Main Content Area

Displays the content for the selected navigation item with context-sensitive tools and actions.

### Dashboard

The Dashboard provides an at-a-glance view of your download activity:

#### Statistics Cards

- **Total Tasks**: Number of download tasks created
- **Active Downloads**: Currently running downloads
- **Completed**: Successfully finished downloads
- **Average Speed**: Average download speed across all tasks

#### Quick Actions

- **New Download**: Start a new download task
- **Batch Import**: Import multiple URLs from a file
- **Clear Cache**: Clean up temporary files
- **Settings**: Quick access to configuration

#### Recent Activity

- List of recent download tasks with status
- Quick action buttons for each task
- Progress indicators for active downloads

### Download Manager

The Download Manager is where you control all your download tasks:

#### Task List

- **Sortable columns**: Name, Status, Progress, Speed, Size
- **Filter options**: All, Running, Paused, Completed, Failed
- **Search functionality**: Find tasks by name or URL
- **Bulk actions**: Start/pause/cancel multiple tasks

#### Task Details Panel

- **Task Information**: Name, URL, file size, duration
- **Progress Visualization**: Progress bar with percentage
- **Speed Metrics**: Current and average download speeds
- **Real-time Logs**: Live log output for the selected task

### Activity Logs

Comprehensive logging interface for monitoring application activity:

#### Log Display

- **Filterable by level**: Debug, Info, Warning, Error
- **Search capability**: Find specific log entries
- **Time range filtering**: Show logs from specific time periods
- **Export options**: Save logs to file for analysis

#### Statistics

- **Log level distribution**: Visual breakdown of log types
- **Recent activity**: Latest log entries
- **Performance metrics**: System resource usage

## Downloading Videos

### Basic Download

To start a basic download:

1. **Navigate to Dashboard** or **Download Manager**
2. **Click "New Download"** button
3. **Enter the video URL** in the dialog box
4. **Choose output location** (optional - uses default if not specified)
5. **Click "Start Download"**

The application will:

- Analyze the URL to detect video streams
- Show available quality options (if multiple)
- Begin downloading segments automatically
- Display real-time progress

### Supported URL Types

VidTanium supports various video URL formats:

#### Direct M3U8 Links

```
https://example.com/video/playlist.m3u8
https://stream.example.com/live/index.m3u8?token=abc123
```

#### Web Pages with Embedded Videos

```
https://video-site.com/watch?v=abc123
https://streaming-platform.com/video/episode-1
```

#### API Endpoints

```
https://api.example.com/video/stream?id=123
https://cdn.example.com/manifest/video.json
```

### Download Options

When creating a new download task, you can configure:

#### Basic Options

- **Video URL**: The source URL for the video
- **Output File**: Where to save the downloaded video
- **Quality**: Select from available quality options
- **Priority**: Set task priority (Low, Normal, High)

#### Advanced Options

- **Custom Headers**: Add HTTP headers for authentication
- **Proxy Settings**: Use proxy for this specific download
- **Retry Settings**: Configure retry attempts and delays
- **Segment Range**: Download specific segment ranges

### Quality Selection

For streams with multiple quality options:

1. **Automatic Selection**: VidTanium picks the best available quality
2. **Manual Selection**: Choose specific resolution and bitrate
3. **Custom Parameters**: Set custom quality criteria

Quality options typically include:

- **Resolution**: 1080p, 720p, 480p, 360p
- **Bitrate**: Higher bitrate = better quality, larger file
- **Codec**: Video encoding format (H.264, H.265, etc.)
- **Audio Quality**: Audio bitrate and format

### Encrypted Content

VidTanium automatically handles encrypted video streams:

#### Supported Encryption

- **AES-128**: Standard HLS encryption
- **Sample-AES**: Apple's sample-based encryption
- **Custom**: Other encryption methods (limited support)

#### Key Handling

- **Automatic Key Retrieval**: Downloads encryption keys automatically
- **Key Caching**: Reuses keys for efficiency
- **Error Recovery**: Retries key downloads on failure

The decryption process is transparent - you don't need to do anything special for encrypted content.

## Managing Downloads

### Task Control

Each download task can be controlled individually:

#### Task Actions

- **Start**: Begin or resume download
- **Pause**: Temporarily stop download (can be resumed)
- **Cancel**: Stop and remove download task
- **Retry**: Restart failed downloads
- **Remove**: Delete completed tasks from list

#### Bulk Operations

Select multiple tasks to perform actions on all at once:

- **Start All**: Begin all pending downloads
- **Pause All**: Pause all active downloads
- **Clear Completed**: Remove all finished tasks

### Download States

Downloads progress through various states:

#### Pending

- Task created but not yet started
- Waiting in queue for available slot
- Can be started manually or automatically

#### Running

- Actively downloading video segments
- Progress updates in real-time
- Can be paused or cancelled

#### Paused

- Download temporarily stopped
- Progress preserved for resuming
- Can be resumed or cancelled

#### Completed

- Download finished successfully
- Video file ready for use
- Can be removed from task list

#### Failed

- Download encountered unrecoverable error
- Error details available in logs
- Can be retried or removed

#### Cancelled

- Download stopped by user action
- Partial files may be preserved
- Can be restarted as new task

### Progress Monitoring

Monitor download progress through multiple indicators:

#### Progress Bar

- **Visual representation**: Percentage complete
- **Color coding**: Green (good), Yellow (warning), Red (error)
- **Animation**: Smooth progress updates

#### Statistics Display

- **Download Speed**: Current and average speeds
- **Time Remaining**: Estimated completion time
- **Segments Progress**: Completed vs. total segments
- **File Size**: Downloaded vs. total size

#### Real-time Logs

- **Live updates**: See download activity as it happens
- **Error messages**: Immediate notification of issues
- **Performance data**: Speed and efficiency metrics

## Media Processing

VidTanium includes powerful media processing capabilities for working with downloaded videos.

### Format Conversion

Convert videos between different formats:

#### Supported Formats

- **Input**: MP4, MKV, AVI, MOV, TS, M4V, WMV, FLV, WEBM
- **Output**: MP4, MKV, AVI, MOV, WEBM

#### Conversion Process

1. **Select Input File**: Choose video to convert
2. **Choose Output Format**: Select target format
3. **Configure Settings**: Adjust quality and encoding options
4. **Start Conversion**: Process runs in background

#### Quality Settings

- **Video Codec**: H.264, H.265, VP9
- **Resolution**: Maintain original or scale to specific size
- **Bitrate**: Control file size vs. quality trade-off
- **Frame Rate**: Adjust playback smoothness

### Video Editing

Edit downloaded videos without external software:

#### Clipping

Extract specific segments from videos:

- **Start Time**: When to begin clip (HH:MM:SS format)
- **Duration**: How long the clip should be
- **Precision**: Frame-accurate cutting
- **Quality**: Maintain original quality

#### Audio Extraction

Extract audio tracks from videos:

- **Format Options**: MP3, AAC, WAV, OGG
- **Quality Settings**: Bitrate selection
- **Metadata**: Preserve title, artist, etc.

#### Compression

Reduce file size while maintaining quality:

- **Quality Mode**: Set target quality level
- **Size Mode**: Specify target file size
- **Advanced Options**: Custom encoding parameters

### Batch Processing

Process multiple files simultaneously:

#### Batch Conversion

1. **Add Files**: Select multiple videos to convert
2. **Choose Settings**: Apply same settings to all files
3. **Configure Output**: Set output directory and naming
4. **Start Processing**: Convert all files automatically

#### Automation

- **Watch Folders**: Automatically process new files
- **Custom Scripts**: Run external processing tools
- **Workflow Templates**: Save and reuse processing configurations

## Settings & Configuration

### General Settings

#### Application Behavior

- **Auto Start**: Launch VidTanium on system startup
- **Minimize to Tray**: Hide to system tray when minimized
- **Check Updates**: Automatically check for new versions
- **Language**: Choose interface language

#### File Management

- **Default Download Location**: Where to save downloaded files
- **Auto Cleanup**: Remove temporary files after download
- **File Naming**: Template for naming downloaded files
- **Folder Organization**: Automatic folder creation and organization

### Download Settings

#### Performance

- **Concurrent Downloads**: Number of simultaneous downloads (1-10)
- **Segments per Task**: How many segments to download in parallel
- **Retry Attempts**: Maximum number of retry attempts for failed segments
- **Retry Delay**: Time to wait between retry attempts

#### Network

- **Request Timeout**: Maximum time to wait for server response
- **Chunk Size**: Size of download chunks for optimization
- **User Agent**: Custom user agent string for requests
- **Connection Limits**: Maximum connections per host

### Network Configuration

#### Proxy Settings

- **HTTP Proxy**: Configure HTTP proxy server
- **HTTPS Proxy**: Configure HTTPS proxy server
- **Authentication**: Username/password for proxy
- **Bypass List**: URLs to access directly

#### Security

- **SSL Verification**: Verify SSL certificates
- **Certificate Path**: Custom certificate bundle
- **TLS Version**: Minimum TLS version to use

### Interface Settings

#### Theme & Appearance

- **Theme Mode**: Light, Dark, or Auto (follows system)
- **Accent Color**: Customize application accent color
- **Font Size**: Adjust interface text size
- **Compact Mode**: Reduce interface spacing

#### Notifications

- **Desktop Notifications**: Show system notifications
- **Sound Alerts**: Play sounds for events
- **Notification Duration**: How long to show notifications
- **Event Types**: Which events trigger notifications

### Advanced Settings

#### Debugging

- **Debug Mode**: Enable detailed logging
- **Log Level**: Set minimum log level to display
- **Log Retention**: How long to keep log files
- **Performance Monitoring**: Track application performance

#### Experimental Features

- **Beta Features**: Enable experimental functionality
- **Custom Plugins**: Load third-party extensions
- **API Access**: Enable external API access

## Troubleshooting

### Common Issues

#### Download Failures

**Problem**: "All segments failed to download"

**Possible Causes**:

- Network connectivity issues
- Server blocking requests
- Invalid or expired URLs
- Proxy configuration problems

**Solutions**:

1. Check your internet connection
2. Try a different network (mobile hotspot, VPN)
3. Verify the video URL is still valid
4. Disable proxy settings temporarily
5. Check firewall/antivirus blocking

**Problem**: "Encryption key download failed"

**Possible Causes**:

- Key server is down or blocking requests
- Authentication required for key access
- Geo-blocking restrictions

**Solutions**:

1. Check if the video works in a browser
2. Try using a VPN to change location
3. Add appropriate headers (Referer, User-Agent)
4. Contact the content provider

#### Performance Issues

**Problem**: Downloads are very slow

**Possible Causes**:

- Too many concurrent downloads
- Network bandwidth limitations
- Server throttling
- System resource constraints

**Solutions**:

1. Reduce concurrent download limit
2. Pause other network-intensive applications
3. Check system resource usage (CPU, RAM)
4. Try downloading during off-peak hours
5. Adjust chunk size settings

**Problem**: Application freezes or becomes unresponsive

**Possible Causes**:

- Too many large downloads
- Memory leak or resource exhaustion
- UI thread blocking

**Solutions**:

1. Restart the application
2. Reduce number of active downloads
3. Clear completed tasks regularly
4. Check available system memory
5. Enable auto-cleanup in settings

#### File Issues

**Problem**: Downloaded files are corrupted or won't play

**Possible Causes**:

- Incomplete downloads
- Network errors during download
- Codec compatibility issues
- Disk space exhaustion

**Solutions**:

1. Re-download the video
2. Check available disk space
3. Try a different video player
4. Check file integrity in logs
5. Verify output format settings

### Error Messages

#### Network Errors

- **Connection Timeout**: Server took too long to respond
- **Connection Refused**: Server is not accepting connections
- **DNS Resolution Failed**: Cannot resolve server hostname
- **SSL Certificate Error**: Invalid or expired security certificate

#### Authentication Errors

- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Access denied
- **429 Too Many Requests**: Rate limiting active

#### File System Errors

- **Permission Denied**: Insufficient file system permissions
- **Disk Full**: Not enough space for download
- **Path Not Found**: Invalid output directory

### Diagnostic Tools

#### Log Analysis

1. **Open Activity Logs** section
2. **Filter by Error level** to see only problems
3. **Search for specific error messages**
4. **Export logs** for technical support

#### Network Testing

1. **Test URL accessibility** in a web browser
2. **Try different network connections**
3. **Use network monitoring tools** to check connectivity
4. **Verify proxy settings** if applicable

#### System Information

Check system resources:

- **Memory Usage**: Task Manager (Windows) or Activity Monitor (Mac)
- **Disk Space**: File Explorer properties
- **Network Speed**: Online speed test tools
- **Firewall Status**: Security software logs

### Getting Help

#### Self-Help Resources

- **User Manual**: This document
- **FAQ**: Frequently asked questions on website
- **Video Tutorials**: Step-by-step guides
- **Community Forum**: User discussions and tips

#### Technical Support

- **Issue Tracker**: Report bugs on GitHub
- **Email Support**: <support@vidtanium.dev>
- **Documentation**: Complete API and technical docs
- **Development Chat**: Real-time help for advanced users

When reporting issues, include:

- **VidTanium version**
- **Operating system version**
- **Error messages** (copy from logs)
- **Steps to reproduce** the problem
- **Network configuration** (proxy, VPN, etc.)

## Tips & Best Practices

### Optimizing Downloads

#### Performance Tips

1. **Limit Concurrent Downloads**: Start with 3-5 simultaneous downloads
2. **Adjust Based on Network**: More for fast connections, fewer for slow
3. **Monitor System Resources**: Watch CPU and memory usage
4. **Use Auto-Cleanup**: Prevent disk space issues
5. **Schedule Large Downloads**: Use off-peak hours for big files

#### Quality vs. Speed

- **Choose Appropriate Quality**: Higher quality = longer download time
- **Consider Storage Space**: Balance quality against available disk space
- **Use Progressive Download**: Start with lower quality, upgrade later
- **Monitor Speed**: Adjust settings if downloads are too slow

### Organization

#### File Management

1. **Use Descriptive Names**: Include date, source, or quality in filenames
2. **Organize by Categories**: Create folders for different types of content
3. **Regular Cleanup**: Remove old or unwanted downloads
4. **Backup Important Files**: Keep copies of valuable content
5. **Use Consistent Naming**: Develop a standard naming convention

#### Task Management

- **Set Priorities**: Use priority levels for important downloads
- **Group Related Tasks**: Download related content together
- **Monitor Progress**: Check tasks regularly
- **Clean Up Completed**: Remove finished tasks to reduce clutter

### Security & Privacy

#### Safe Downloading

1. **Verify Sources**: Only download from trusted websites
2. **Use HTTPS**: Prefer secure connections when available
3. **Check File Integrity**: Verify downloads completed successfully
4. **Scan for Malware**: Run antivirus scans on downloaded files
5. **Respect Copyright**: Only download content you have rights to use

#### Privacy Protection

- **Use VPN**: Hide your location and activity
- **Custom User Agents**: Avoid detection or blocking
- **Proxy Servers**: Route traffic through intermediary servers
- **Clear Logs**: Regularly clear download history if needed

### Troubleshooting Prevention

#### Proactive Measures

1. **Regular Updates**: Keep VidTanium updated to latest version
2. **Monitor Logs**: Check for warnings before they become errors
3. **Test Small Downloads**: Verify settings with small files first
4. **Backup Settings**: Export configuration before major changes
5. **Monitor System Health**: Keep OS and drivers updated

#### Best Practices

- **Start Simple**: Begin with basic downloads before using advanced features
- **One Change at a Time**: Don't modify multiple settings simultaneously
- **Document Issues**: Keep notes on problems and solutions
- **Learn from Logs**: Study successful downloads to understand patterns
- **Stay Informed**: Follow updates and community discussions

### Advanced Usage

#### Power User Features

1. **Batch Operations**: Use bulk actions for efficiency
2. **Custom Scripts**: Automate repetitive tasks
3. **API Integration**: Connect with other applications
4. **Plugin Development**: Create custom extensions
5. **Advanced Filtering**: Use complex search and filter criteria

#### Automation

- **Watch Folders**: Automatically process new URLs
- **Scheduled Downloads**: Set up recurring download tasks
- **Integration**: Connect with download managers or media servers
- **Scripting**: Use command-line interface for automation

This user manual provides comprehensive guidance for using VidTanium effectively. For technical details and advanced configuration, refer to the Developer Guide and API Reference.
