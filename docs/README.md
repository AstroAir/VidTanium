# VidTanium Documentation

This directory contains the complete documentation for VidTanium, built with [MkDocs](https://www.mkdocs.org/) and the [Material theme](https://squidfunk.github.io/mkdocs-material/).

## 📁 Structure

```
docs/
├── index.md                 # Home page
├── getting-started.md       # Quick start guide
├── installation.md          # Installation instructions
├── workflow-guide.md        # Complete workflow guide
├── user-manual.md          # Detailed user manual
├── examples.md             # Practical examples
├── api-reference.md        # API documentation
├── developer-guide.md      # Development guide
├── project-structure.md    # Project organization
├── documentation.md        # Technical documentation
├── help-system.md         # Help system documentation
├── help/                  # Multi-language help
│   ├── en/               # English help files
│   └── zh_CN/           # Chinese help files
├── stylesheets/          # Custom CSS
└── javascripts/          # Custom JavaScript
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip or uv package manager

### Installation

1. **Install MkDocs and dependencies:**
   ```bash
   pip install -r requirements-docs.txt
   ```

2. **Preview the documentation:**
   ```bash
   mkdocs serve
   ```
   
   Open http://127.0.0.1:8000 in your browser.

3. **Build for production:**
   ```bash
   mkdocs build
   ```

## 🛠️ Development

### Local Development

```bash
# Start development server with live reload
mkdocs serve

# Build and serve on custom port
mkdocs serve --dev-addr=127.0.0.1:8080

# Build with strict mode (fail on warnings)
mkdocs build --strict

# Clean build directory
mkdocs build --clean
```

### Testing

Run the documentation test suite:

```bash
python scripts/test-docs.py
```

This will check:
- MkDocs installation
- Configuration validity
- File existence
- Build process
- Internal links

### Adding New Pages

1. **Create the markdown file** in the `docs/` directory
2. **Add front matter** (optional but recommended):
   ```yaml
   ---
   title: Page Title
   description: Page description for SEO
   ---
   ```
3. **Update navigation** in `mkdocs.yml`:
   ```yaml
   nav:
     - Section Name:
       - Page Name: filename.md
   ```

### Markdown Extensions

The documentation supports these extensions:

- **Admonitions**: `!!! note`, `!!! warning`, etc.
- **Code highlighting**: Syntax highlighting for 100+ languages
- **Tabbed content**: `=== "Tab 1"` syntax
- **Task lists**: `- [x] Completed task`
- **Tables**: Standard markdown tables
- **Math**: LaTeX math expressions
- **Mermaid diagrams**: Flowcharts and diagrams

### Custom Styling

- **CSS**: Add custom styles to `docs/stylesheets/extra.css`
- **JavaScript**: Add custom scripts to `docs/javascripts/`
- **Theme colors**: Configure in `mkdocs.yml` under `theme.palette`

## 📝 Writing Guidelines

### Style Guide

1. **Use clear, concise headings**
2. **Include code examples** for technical content
3. **Add admonitions** for important notes
4. **Use tables** for structured data
5. **Include cross-references** between related pages

### Admonition Types

```markdown
!!! note "Optional Title"
    Information note

!!! tip "Pro Tip"
    Helpful tip

!!! warning "Important"
    Warning message

!!! danger "Critical"
    Critical warning

!!! example "Example"
    Code example

!!! info "Information"
    General information
```

### Code Blocks

```markdown
```python title="example.py"
def hello_world():
    print("Hello, World!")
```
```

### Tabbed Content

```markdown
=== "Python"
    ```python
    print("Hello from Python")
    ```

=== "JavaScript"
    ```javascript
    console.log("Hello from JavaScript");
    ```
```

## 🚀 Deployment

### GitHub Pages

The documentation is automatically deployed to GitHub Pages via GitHub Actions when changes are pushed to the main branch.

### Manual Deployment

```bash
# Build the site
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy

# Deploy to custom domain
mkdocs build
# Upload the 'site' directory to your web server
```

### Other Platforms

The built site in the `site/` directory can be deployed to:

- **Netlify**: Connect your GitHub repo and set build command to `mkdocs build`
- **Vercel**: Similar to Netlify
- **AWS S3**: Upload the `site/` directory
- **Any web server**: Upload the `site/` directory

## 🔧 Configuration

Key configuration options in `mkdocs.yml`:

```yaml
# Site information
site_name: VidTanium Documentation
site_description: Documentation description
site_url: https://your-domain.com

# Theme configuration
theme:
  name: material
  palette:
    - scheme: default
      primary: teal
      accent: cyan

# Navigation structure
nav:
  - Home: index.md
  - Getting Started: getting-started.md
  # ... more pages

# Extensions
markdown_extensions:
  - admonition
  - pymdownx.highlight
  - pymdownx.superfences
  # ... more extensions
```

## 📊 Analytics

The documentation includes:

- **Search functionality** with full-text search
- **Page feedback** system
- **Social links** to GitHub repository
- **Edit page** links for contributors

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes** to the documentation
4. **Test locally** with `mkdocs serve`
5. **Run tests** with `python scripts/test-docs.py`
6. **Submit a pull request**

## 📚 Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material Theme Documentation](https://squidfunk.github.io/mkdocs-material/)
- [Markdown Guide](https://www.markdownguide.org/)
- [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/)

## 🆘 Troubleshooting

### Common Issues

**Build fails with "Config value 'theme' error":**
```bash
pip install mkdocs-material
```

**Serve command fails:**
```bash
# Check if port is in use
lsof -i :8000

# Use different port
mkdocs serve --dev-addr=127.0.0.1:8080
```

**Links not working:**
- Check file paths are relative to `docs/` directory
- Ensure `.md` extension is included in links
- Use forward slashes `/` even on Windows

**Styling not applied:**
- Check `extra_css` paths in `mkdocs.yml`
- Ensure CSS files exist in `docs/stylesheets/`
- Clear browser cache

For more help, see the [troubleshooting guide](workflow-guide.md#troubleshooting) or [open an issue](https://github.com/AstroAir/VidTanium/issues).
