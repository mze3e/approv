# approv
An open source workflow engine built on python with duckdb

## Address parser CLI (pypostal/libpostal)

This repo includes a small CLI that splits an address into components using
pypostal/libpostal.

### Usage (Python)

```bash
python -m address_parser.cli "1600 Amphitheatre Parkway, Mountain View, CA 94043"
```

### Build a Windows 64-bit standalone exe

1. Install libpostal and the Python dependencies (postal + pyinstaller):

```powershell
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

> Note: `postal` is a wrapper around libpostal. Ensure libpostal is available on
> your build machine so the package can locate the shared library before
> building the exe.

2. Build the standalone executable:

```powershell
pyinstaller --onefile --name address_parser `
  --collect-binaries postal `
  --collect-submodules postal `
  address_parser/cli.py
```

Or use the helper script:

```powershell
scripts\\build_address_parser.ps1
```

3. Run the exe on any Windows 64-bit machine (no external dependencies needed):

```powershell
dist\\address_parser.exe "1600 Amphitheatre Parkway, Mountain View, CA 94043"
```
