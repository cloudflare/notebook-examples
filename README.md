# Notebook Examples

Interactive Python notebooks demonstrating Cloudflare services, APIs, and workflows. These examples cover tasks from analyzing logs to writing billing reports, storing files in [R2](https://www.cloudflare.com/developer-platform/products/r2/), querying [D1](https://developers.cloudflare.com/d1/) databases, and more!


## 🛠️ Development

### Prerequisites
- [Python 3.8+](https://www.python.org/downloads/)
- [Node.js](https://nodejs.org/) for WASM builds
- [Git](https://git-scm.com/downloads)

### Python Packages
- [marimo](https://pypi.org/project/marimo/) notebook server
- [moutils](https://pypi.org/project/moutils/) OAuth login and other utilities
- [uv](https://pypi.org/project/uv/) for uv builds

### Running Notebooks

#### notebooks.cloudflare.com

Visit [notebooks.cloudflare.com](https://notebooks.cloudflare.com/) to run notebooks directly in your browser using WASM.

This deployment is automatic whenever changes are merged to the `main` branch

#### Python Development Mode
```bash
make edit
```
- Starts Marimo server on http://localhost:2718
- Full Python environment with all packages
- Best for development and testing

#### WASM Preview Mode
```bash
make export
make preview
```
- Builds notebooks for web deployment
- Runs locally to preview WASM version
- Matches production environment

#### Single Notebook Mode
```bash
# Using Python venv
make edit-notebook notebook=_start.py

# Using uv (faster setup)
make edit-uv-notebook notebook=_start.py
```

### Available Commands
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛠  Running: help
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Main workflow:
edit                 [PYTHON][WORKSPACE][*] Launch marimo edit in workspace mode
export               [WASM BUILD][*] Build HTML/WASM and show preview instructions
preview              [WASM SERVE][*] Serve the exported notebooks locally

Other commands:
clean-deep           Deep clean including removal of the Python virtual environment
clean                Remove temporary files, caches, and build artifacts
deploy               Run lint, build HTML/WASM, and deploy via npm
edit-notebook        [PYTHON][NOTEBOOK] Launch marimo edit for a specific notebook (default: _start.py)
edit-uv-notebook     [PYTHON][NOTEBOOK] Launch marimo with uv for a specific notebook (default: _start.py)
edit-uv-workspace    [PYTHON][WORKSPACE] Launch marimo with uv in workspace mode
lint                 Run Python and JavaScript linters
venv                 Alias to set up Python virtual environment
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to this project.

## 📝 Adding New Notebooks

1. **Create your notebook** in the `notebooks/` directory
2. **Add to configuration** in `notebooks.yaml`:
   ```yaml
   - title: "My New Notebook"
     description: "Description of what it does"
     file: "my_notebook.py"
   ```
3. **Test python locally**: `make edit`
4. **Test WASM locally**: `make export && make preview` 
5. **Submit a PR** with your changes. See

## 🔧 Technical Details

### Architecture
- **Local Development**: Python virtual environment with Marimo
- **Web Deployment**: WASM compilation using Pyodide
- **Hosting**: Cloudflare Workers at [notebooks.cloudflare.com](https://notebooks.cloudflare.com)

### Package Management
- **Local**: Standard pip/requirements.txt
- **WASM**: Pre-installed packages in Pyodide (see [package list](https://pyodide.org/en/stable/usage/packages-in-pyodide.html))

## 📖 Documentation

- **[Cloudflare API Docs](https://developers.cloudflare.com/api/)**: Complete API reference
- **[Marimo Documentation](https://docs.marimo.io/)**: Notebook framework guide
- **[Pyodide Documentation](https://pyodide.org/)**: Python in the browser

## 🐛 Troubleshooting

### Common Issues

**"Command not found: make"**
- Install Make: `brew install make` (macOS) or `apt-get install make` (Ubuntu)

**Port 2718 already in use**
- Kill existing process: `lsof -ti:2718 | xargs kill`
- Or use different port: `make edit` (edit Makefile to change port)

**WASM build fails**
- Clean and rebuild: `make clean && make export`
- Check package compatibility with Pyodide (see [package list](https://pyodide.org/en/stable/usage/packages-in-pyodide.html))

**Virtual environment issues**
- Recreate environment: `make clean-deep && make venv`

## 📞 Community

Connect with Cloudflare and the community:

- **Discord**: [Join our Discord server](https://discord.gg/cloudflare)
- **Twitter**: [@Cloudflare](https://twitter.com/cloudflare) and [@CloudflareDev](https://twitter.com/cloudflaredev)
- **GitHub**: [Cloudflare organization](https://github.com/cloudflare)
- **Blog**: [Cloudflare Blog](https://blog.cloudflare.com/)
- **Developer Hub**: [developers.cloudflare.com](https://developers.cloudflare.com/)
