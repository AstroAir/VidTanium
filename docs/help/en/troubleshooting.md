# Troubleshooting Guide

Solutions to common issues and problems you might encounter while using VidTanium.

## Common Issues

### Download Problems

#### Downloads Won't Start

**Symptoms**: Tasks are created but don't begin downloading

**Solutions**:
1. **Check URL validity**: Ensure the URL is accessible in a web browser
2. **Network connectivity**: Verify internet connection is working
3. **Proxy settings**: If using a proxy, verify configuration
4. **Firewall/Antivirus**: Check if software is blocking VidTanium
5. **Restart application**: Close and reopen VidTanium

#### Downloads Keep Failing

**Symptoms**: Downloads start but fail repeatedly

**Solutions**:
1. **Check error logs**: Review Activity Logs for specific error messages
2. **Reduce concurrent downloads**: Lower the number of simultaneous downloads
3. **Adjust retry settings**: Increase retry attempts in settings
4. **Network stability**: Use wired connection if possible
5. **Server issues**: The source server might be overloaded or blocking requests

#### Slow Download Speeds

**Symptoms**: Downloads are much slower than expected

**Solutions**:
1. **Check internet speed**: Test your connection speed
2. **Reduce concurrent downloads**: Fewer simultaneous downloads = higher individual speeds
3. **Adjust thread count**: Increase threads per download for M3U8 files
4. **Server limitations**: Source server might have speed limits
5. **Network congestion**: Try downloading at different times

### Application Issues

#### Application Won't Start

**Symptoms**: VidTanium fails to launch or crashes immediately

**Solutions**:
1. **Check Python version**: Ensure Python 3.11+ is installed
2. **Dependencies**: Verify all required packages are installed
3. **Permissions**: Ensure proper file/folder permissions
4. **Corrupted files**: Reinstall the application
5. **System resources**: Check available memory and disk space

#### Interface Problems

**Symptoms**: UI elements not displaying correctly or application freezes

**Solutions**:
1. **Restart application**: Close and reopen VidTanium
2. **Clear cache**: Delete temporary files and restart
3. **Theme issues**: Try switching between light/dark themes
4. **Display settings**: Check system display scaling settings
5. **Graphics drivers**: Update graphics drivers

#### Settings Not Saving

**Symptoms**: Configuration changes are lost after restart

**Solutions**:
1. **File permissions**: Ensure write access to config directory
2. **Disk space**: Check available storage space
3. **Antivirus interference**: Temporarily disable real-time protection
4. **Manual backup**: Export settings before making changes
5. **Reset to defaults**: Clear all settings and reconfigure

### Network Issues

#### Proxy Configuration Problems

**Symptoms**: Downloads fail when using proxy settings

**Solutions**:
1. **Verify proxy details**: Check server address, port, and credentials
2. **Test proxy**: Verify proxy works with other applications
3. **Authentication**: Ensure username/password are correct
4. **Proxy type**: Confirm HTTP/HTTPS/SOCKS proxy type
5. **Bypass proxy**: Try downloading without proxy temporarily

#### SSL/Certificate Errors

**Symptoms**: HTTPS downloads fail with certificate errors

**Solutions**:
1. **Update certificates**: Ensure system certificates are current
2. **Time/date**: Verify system clock is accurate
3. **Firewall settings**: Check if firewall is interfering
4. **Antivirus SSL scanning**: Disable SSL/TLS scanning temporarily
5. **Alternative URLs**: Try different source URLs if available

### File and Storage Issues

#### Insufficient Disk Space

**Symptoms**: Downloads fail due to lack of storage

**Solutions**:
1. **Free up space**: Delete unnecessary files
2. **Change location**: Use different drive with more space
3. **Cleanup**: Remove incomplete/failed downloads
4. **Monitor usage**: Enable disk space monitoring
5. **External storage**: Use external drive for downloads

#### File Access Errors

**Symptoms**: Cannot write to download directory

**Solutions**:
1. **Permissions**: Ensure write access to target directory
2. **Directory exists**: Verify download folder exists
3. **Path length**: Avoid extremely long file paths
4. **Special characters**: Remove special characters from filenames
5. **Antivirus scanning**: Exclude download folder from real-time scanning

## Error Messages

### Common Error Codes

#### Network Errors
- **Connection timeout**: Server not responding - try again later
- **DNS resolution failed**: Check internet connection and DNS settings
- **Connection refused**: Server is blocking connections
- **SSL handshake failed**: Certificate or encryption issues

#### File System Errors
- **Permission denied**: Insufficient file/folder permissions
- **Disk full**: No available storage space
- **Path not found**: Download directory doesn't exist
- **File in use**: Target file is locked by another process

#### Application Errors
- **Memory error**: Insufficient RAM - close other applications
- **Configuration error**: Settings file corrupted - reset to defaults
- **Dependency missing**: Required library not installed
- **Version mismatch**: Incompatible component versions

## Getting Additional Help

### Diagnostic Information

When reporting issues, include:

1. **Application version**: Check About dialog
2. **Operating system**: Version and architecture
3. **Error messages**: Exact text from error dialogs
4. **Log files**: Recent entries from Activity Logs
5. **Steps to reproduce**: What you were doing when the issue occurred

### Log Files

Important log locations:
- **Application logs**: Available in Activity Logs viewer
- **System logs**: Check system event logs
- **Network logs**: Enable debug logging for network issues

### Support Resources

1. **Built-in Help**: This help system
2. **Activity Logs**: Detailed operation logs
3. **GitHub Issues**: Community support and bug reports
4. **Documentation**: Comprehensive guides and API reference

### Before Contacting Support

1. **Check this guide**: Review relevant troubleshooting sections
2. **Search logs**: Look for specific error messages
3. **Try basic solutions**: Restart, check connections, verify settings
4. **Reproduce issue**: Confirm the problem is consistent
5. **Gather information**: Collect diagnostic data

---

If you can't find a solution here, check the [User Guide](user-guide.md) for detailed feature documentation or review the Activity Logs for specific error details.
