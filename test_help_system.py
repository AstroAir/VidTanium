#!/usr/bin/env python3
"""
Test script for VidTanium Help System
Verifies that the help system components work correctly
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

# Import help system components
from src.gui.widgets.help import HelpInterface, MarkdownViewer, HelpNavigationPanel
from src.gui.utils.i18n import get_i18n_manager


class TestHelpWindow(QMainWindow):
    """Test window for help system"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VidTanium Help System Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize i18n
        self.i18n_manager = get_i18n_manager()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create help interface
        try:
            self.help_interface = HelpInterface()
            layout.addWidget(self.help_interface)
            print("✓ Help interface created successfully")
        except Exception as e:
            print(f"✗ Failed to create help interface: {e}")
            return
        
        # Test navigation
        self._test_navigation()
    
    def _test_navigation(self):
        """Test help navigation functionality"""
        print("\nTesting help navigation...")
        
        # Test loading different pages
        test_pages = ["index", "getting-started", "user-guide", "troubleshooting"]
        
        for page in test_pages:
            try:
                self.help_interface.load_page(page)
                print(f"✓ Successfully loaded page: {page}")
            except Exception as e:
                print(f"✗ Failed to load page {page}: {e}")
        
        # Test invalid page
        try:
            self.help_interface.load_page("nonexistent-page")
            print("✗ Should have failed to load nonexistent page")
        except Exception as e:
            print(f"✓ Correctly handled invalid page: {e}")


def test_markdown_viewer():
    """Test markdown viewer component"""
    print("\nTesting Markdown viewer...")
    
    try:
        viewer = MarkdownViewer()
        
        # Test markdown content
        test_content = """
# Test Markdown

This is a **test** of the markdown viewer.

## Features

- Lists work
- *Italic text* works
- `Code blocks` work

### Code Example

```python
def hello_world():
    print("Hello, World!")
```

[Test Link](https://example.com)
"""
        
        viewer.set_markdown_content(test_content)
        print("✓ Markdown content set successfully")
        
        # Test content retrieval
        retrieved_content = viewer.get_markdown_content()
        if retrieved_content == test_content:
            print("✓ Content retrieval works correctly")
        else:
            print("✗ Content retrieval failed")
            
    except Exception as e:
        print(f"✗ Markdown viewer test failed: {e}")


def test_help_navigation_panel():
    """Test help navigation panel"""
    print("\nTesting Help navigation panel...")
    
    try:
        nav_panel = HelpNavigationPanel()
        
        # Test getting available pages
        pages = nav_panel.get_available_pages()
        expected_pages = ["index", "getting-started", "user-guide", "troubleshooting"]
        
        if all(page in pages for page in expected_pages):
            print("✓ Navigation panel has all expected pages")
        else:
            print(f"✗ Missing pages. Expected: {expected_pages}, Got: {pages}")
        
        # Test setting current page
        nav_panel.set_current_page("getting-started")
        if nav_panel.get_current_page() == "getting-started":
            print("✓ Current page setting works correctly")
        else:
            print("✗ Current page setting failed")
            
    except Exception as e:
        print(f"✗ Navigation panel test failed: {e}")


def check_help_files():
    """Check if help documentation files exist"""
    print("\nChecking help documentation files...")
    
    help_base = Path("docs/help")
    
    for locale in ["en", "zh_CN"]:
        locale_path = help_base / locale
        if not locale_path.exists():
            print(f"✗ Help directory missing: {locale_path}")
            continue
        
        required_files = ["index.md", "getting-started.md", "user-guide.md", "troubleshooting.md"]
        
        for file_name in required_files:
            file_path = locale_path / file_name
            if file_path.exists():
                print(f"✓ Found help file: {locale}/{file_name}")
            else:
                print(f"✗ Missing help file: {locale}/{file_name}")


def main():
    """Main test function"""
    print("VidTanium Help System Test")
    print("=" * 40)
    
    # Check help files first
    check_help_files()
    
    # Test individual components
    test_markdown_viewer()
    test_help_navigation_panel()
    
    # Test full interface
    app = QApplication(sys.argv)
    
    try:
        window = TestHelpWindow()
        window.show()
        
        print("\n" + "=" * 40)
        print("Help system test window opened.")
        print("Please verify:")
        print("1. Help interface displays correctly")
        print("2. Navigation panel shows all topics")
        print("3. Clicking navigation items loads content")
        print("4. Markdown content renders properly")
        print("5. Links work correctly")
        print("6. Error handling works for invalid pages")
        print("7. Responsive design adapts to window size")
        print("\nClose the window to complete the test.")
        print("=" * 40)
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"✗ Failed to create test window: {e}")
        return 1


if __name__ == "__main__":
    main()
