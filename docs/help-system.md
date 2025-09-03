# VidTanium Help System

This document describes the implementation of the comprehensive help documentation system for VidTanium.

## Overview

The help system provides users with comprehensive documentation directly within the application, supporting:

- **Markdown Rendering**: Full Markdown support with proper styling
- **Multi-language Support**: English and Chinese documentation
- **Responsive Design**: Adapts to different screen sizes
- **Navigation**: Easy browsing between help topics
- **Error Handling**: Graceful handling of missing or malformed content

## Architecture

### Components

1. **HelpInterface** (`src/gui/widgets/help/help_interface.py`)
   - Main help interface container
   - Manages navigation and content display
   - Handles responsive layout changes

2. **MarkdownViewer** (`src/gui/widgets/help/markdown_viewer.py`)
   - Renders Markdown content with proper styling
   - Supports code highlighting, tables, and links
   - Applies application theme colors

3. **HelpNavigationPanel** (`src/gui/widgets/help/help_navigation.py`)
   - Provides navigation between help topics
   - Shows available help pages with descriptions
   - Handles active page highlighting

### File Structure

```
docs/help/
├── en/                     # English documentation
│   ├── index.md           # Overview and navigation
│   ├── getting-started.md # Quick start guide
│   ├── user-guide.md      # Comprehensive user guide
│   └── troubleshooting.md # Common issues and solutions
└── zh_CN/                 # Chinese documentation
    ├── index.md
    ├── getting-started.md
    ├── user-guide.md
    └── troubleshooting.md
```

## Features

### Markdown Support

The help system supports full Markdown syntax including:

- Headers (H1-H6)
- **Bold** and *italic* text
- Lists (ordered and unordered)
- Code blocks with syntax highlighting
- Tables
- Links (internal and external)
- Blockquotes
- Horizontal rules

### Theming

The Markdown viewer automatically applies the application's design system:

- Adapts to light/dark themes
- Uses consistent colors and fonts
- Responsive typography
- Proper contrast ratios

### Navigation

- **Side Navigation**: Browse help topics easily
- **Internal Links**: Click links in content to navigate
- **Breadcrumbs**: Track current location
- **Search**: Find specific content (future enhancement)

### Internationalization

- **Multi-language**: Supports English and Chinese
- **Automatic Fallback**: Falls back to English if locale content missing
- **Extensible**: Easy to add new languages

## Integration

### Main Application

The help system is integrated into the main application navigation:

```python
# In main_window.py
from .widgets.help import HelpInterface

# Add to navigation
self.addSubInterface(
    self.help_interface,
    FIF.HELP,
    tr('navigation.help'),
    NavigationItemPosition.BOTTOM
)
```

### Routing

Help pages are mapped in the routing system:

```python
NAVIGATION_ROUTES = {
    "/help": "help_interface",
    "/help/index": "help_interface",
    "/help/getting-started": "help_interface",
    "/help/user-guide": "help_interface",
    "/help/troubleshooting": "help_interface",
}
```

## Usage

### Adding New Help Pages

1. **Create Markdown Files**:
   ```bash
   # Add to both language directories
   docs/help/en/new-topic.md
   docs/help/zh_CN/new-topic.md
   ```

2. **Update Navigation**:
   ```python
   # In help_navigation.py, add to help_topics list
   {
       "page_name": "new-topic",
       "title": tr("help.pages.new_topic"),
       "description": tr("help.pages.new_topic_desc"),
       "icon": FIF.DOCUMENT
   }
   ```

3. **Add Translations**:
   ```json
   // In locales/en.json and zh_CN.json
   "help": {
       "pages": {
           "new_topic": "New Topic",
           "new_topic_desc": "Description of new topic"
       }
   }
   ```

### Customizing Styling

The Markdown viewer uses the application's design system. To customize:

1. **Colors**: Modify `DesignSystem.get_color()` calls in `markdown_viewer.py`
2. **Typography**: Update font settings in `_setup_styling()`
3. **Layout**: Adjust margins and spacing in CSS

## Dependencies

- **markdown**: Python Markdown library for parsing
- **PySide6**: Qt framework for UI components
- **qfluentwidgets**: Fluent design components

## Testing

Run the help system test:

```bash
python test_help_system.py
```

This will:
- Verify all components load correctly
- Test Markdown rendering
- Check navigation functionality
- Validate help file existence
- Open a test window for manual verification

## Error Handling

The help system includes comprehensive error handling:

- **Missing Files**: Shows user-friendly error messages
- **Malformed Markdown**: Falls back to plain text
- **Network Issues**: Handles external link failures
- **Component Errors**: Provides fallback interfaces

## Performance

- **Lazy Loading**: Content loaded only when requested
- **Caching**: Parsed content cached for performance
- **Responsive**: Efficient layout updates
- **Memory Management**: Proper cleanup of resources

## Future Enhancements

Potential improvements:

1. **Search Functionality**: Full-text search across help content
2. **Bookmarks**: Save frequently accessed pages
3. **Print Support**: Print help pages
4. **Offline Mode**: Cache content for offline access
5. **Interactive Tutorials**: Step-by-step guided tours
6. **Video Embedding**: Support for video content
7. **Feedback System**: User feedback on help content

## Troubleshooting

### Common Issues

1. **Markdown not rendering**: Ensure `markdown` library is installed
2. **Missing content**: Check file paths and permissions
3. **Styling issues**: Verify design system integration
4. **Navigation problems**: Check translation keys

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger('src.gui.widgets.help').setLevel(logging.DEBUG)
```

## Contributing

When contributing to the help system:

1. **Follow Markdown standards**: Use consistent formatting
2. **Update translations**: Maintain both English and Chinese versions
3. **Test thoroughly**: Verify all functionality works
4. **Document changes**: Update this README for significant changes

---

For more information, see the help content itself by running the application and navigating to Help → Overview.
