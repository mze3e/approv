$ErrorActionPreference = "Stop"

python -m pip install -r requirements.txt
python -m pip install pyinstaller

pyinstaller --onefile --name address_parser `
  --collect-binaries postal `
  --collect-submodules postal `
  address_parser/cli.py
