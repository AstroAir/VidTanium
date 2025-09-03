---
title: VidTanium Documentation
description: A powerful video download tool with built-in player and editor capabilities
---

# VidTanium

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Quick Start**

    ---

    Get up and running with VidTanium in minutes

    [:octicons-arrow-right-24: Installation Guide](installation.md)

-   :material-book-open-page-variant:{ .lg .middle } **User Guide**

    ---

    Complete documentation for end users

    [:octicons-arrow-right-24: User Manual](user-manual.md)

-   :material-code-braces:{ .lg .middle } **Developer Resources**

    ---

    API documentation and development guides

    [:octicons-arrow-right-24: API Reference](api-reference.md)

-   :material-lightbulb:{ .lg .middle } **Examples**

    ---

    Real-world examples and use cases

    [:octicons-arrow-right-24: Examples](examples.md)

</div>

## Overview

VidTanium is a modern, feature-rich video download tool specifically designed for downloading encrypted M3U8 video streams. Built with Python and PySide6, it offers a beautiful Fluent Design interface combined with powerful download capabilities and integrated media processing tools.

### ✨ Key Features

#### Core Download Engine

- **🔐 Encrypted M3U8 Support** - Full AES-128 encryption support with automatic key handling
- **🚀 Multi-threaded Downloads** - High-speed parallel downloading with configurable concurrency
- **🎯 Intelligent Retry System** - Advanced retry management with circuit breaker pattern
- **📊 Smart Queue Management** - Priority-based task scheduling with dynamic optimization
- **🔄 Batch Processing** - Support for batch downloads and URL imports with bulk operations

#### Advanced Monitoring & Analytics

- **📈 Bandwidth Monitoring** - Real-time network performance tracking and optimization
- **⏱️ ETA Calculation** - Multiple algorithms (Linear, Exponential, Adaptive) for accurate time estimates
- **📋 Download History** - Comprehensive tracking and analytics of completed downloads
- **🎯 Progress Aggregation** - Multi-task progress monitoring with detailed statistics
- **🔍 Performance Analytics** - Network interface detection and baseline performance metrics

#### Enhanced Error Handling

- **🛡️ Intelligent Error Recovery** - Categorized error handling with severity levels and context
- **🔧 User-Friendly Diagnostics** - Clear error messages with suggested actions
- **🔄 Circuit Breaker Protection** - Automatic fault tolerance and system protection
- **📝 Error Context Tracking** - Detailed diagnostic information for troubleshooting

#### Modern User Interface

- **🎨 Fluent Design UI** - Beautiful, responsive interface built with PySide6
- **📱 Responsive Layout** - Adaptive UI that works across different screen sizes
- **🎭 Advanced Theme System** - Enhanced theming with system integration
- **📊 Analytics Dashboard** - Comprehensive metrics and performance visualization
- **🔧 Bulk Operations** - Efficient management of multiple download tasks

## Quick Start

!!! tip "New to VidTanium?"
    Start with our [Complete Workflow Guide](workflow-guide.md) for step-by-step instructions from installation to advanced usage.

### Prerequisites

- **Python 3.11+** - [Download here](https://python.org/downloads/)
- **FFmpeg** - Required for media processing
- **4GB RAM minimum** (8GB recommended)
- **Stable internet connection**

### Installation

=== "Using uv (Recommended)"

    ```bash
    # Install uv package manager
    curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
    # or
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

    # Clone and install VidTanium
    git clone https://github.com/AstroAir/VidTanium.git
    cd VidTanium
    uv sync
    ```

=== "Using pip"

    ```bash
    git clone https://github.com/AstroAir/VidTanium.git
    cd VidTanium
    pip install -e .
    ```

### Your First Download

1. **Launch VidTanium**: `python main.py`
2. **Paste M3U8 URL** in the input field
3. **Click "Add Task"** to start downloading
4. **Monitor progress** in real-time

## Documentation Structure

### 📚 User Documentation

| Document | Purpose | Best For |
|----------|---------|----------|
| [🚀 **Workflow Guide**](workflow-guide.md) | **Complete end-to-end guide** | **All users - start here!** |
| [⚙️ Installation Guide](installation.md) | Setup and configuration | New users, system administrators |
| [📋 User Manual](user-manual.md) | Complete user guide with advanced features | End users, power users |
| [💡 Examples](examples.md) | Practical examples and use cases | Users wanting real-world scenarios |
| [🐛 Help System](help-system.md) | Built-in help and troubleshooting | Users experiencing issues |

### 👨‍💻 Developer Documentation

| Document | Purpose | Best For |
|----------|---------|----------|
| [🔧 Developer Guide](developer-guide.md) | Development setup and architecture | Contributors, maintainers |
| [📚 API Reference](api-reference.md) | Comprehensive API documentation | Developers, integrators |
| [🏗️ Project Structure](project-structure.md) | Project organization and components | New contributors, architects |
| [📖 Technical Documentation](documentation.md) | In-depth technical details | Advanced developers, researchers |

## Quick Navigation Paths

!!! example "Choose Your Path"

    === "🆕 New Users"
        1. [**Workflow Guide**](workflow-guide.md) - Complete step-by-step guide
        2. [Installation](installation.md) - Detailed setup instructions
        3. [First Download](workflow-guide.md#your-first-download) - Get started immediately
        4. [Examples](examples.md) - Learn from practical scenarios

    === "👨‍💻 Developers"
        1. [**Workflow Guide**](workflow-guide.md) - Understand the complete system
        2. [API Examples](examples.md#integration-examples) - See real implementations
        3. [API Reference](api-reference.md) - Detailed technical documentation
        4. [Developer Guide](developer-guide.md) - Contribute to the project

    === "⚡ Power Users"
        1. [**Workflow Guide**](workflow-guide.md) - Master the system
        2. [Advanced Examples](examples.md#advanced-workflows) - Complex scenarios
        3. [Performance Optimization](examples.md#performance-optimization) - Maximize efficiency
        4. [Custom Integration](examples.md#integration-examples) - Build solutions

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: Version 3.11 or higher
- **RAM**: 4 GB minimum, 8 GB recommended
- **Storage**: 500 MB for application, additional space for downloads
- **Network**: Internet connection required for downloads

### Recommended Requirements

- **RAM**: 16 GB for optimal performance with large files
- **Storage**: SSD for better performance
- **CPU**: Multi-core processor for concurrent downloads
- **Graphics**: Hardware acceleration support for media processing

## Support

- 📖 [Complete Documentation](workflow-guide.md)
- 🐛 [Issue Tracker](https://github.com/AstroAir/VidTanium/issues)
- 💬 [Discussions](https://github.com/AstroAir/VidTanium/discussions)
- 📧 Email: support@vidtanium.com

---

!!! success "Ready to get started?"
    Jump to the [Installation Guide](installation.md) or explore the [Complete Workflow Guide](workflow-guide.md) for comprehensive instructions.
