# 🚀 Publishing FixFlow to PyPI manually

Since the automated publish process might be stuck, please run this command manually in your terminal:

```bash
uv publish --token pypi-<YOUR_TOKEN_HERE>
```

Or if `uv` is installed via pip:

```bash
python -m uv publish --token pypi-<YOUR_TOKEN_HERE>
```

Once published, you verify it here:
https://pypi.org/project/fixflow-mcp/
