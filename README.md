#### Preview
![preview.png](img/preview.jpg)

### Checking application authenticity
Always check the authenticity of any application you are downloading over the internet. By utilizing the following commands, you are ensuring the application you have downloaded hasn't been modified/tampered and should match the values below.

**Windows:** `certutil -hashfile bitgreen-airdrop-verifier-windows.zip`
```
SHA1 hash of bitgreen-airdrop-verifier-windows.zip:
d82e8862157ca07b9866bdf610349d3766d3ad53
CertUtil: -hashfile command completed successfully.
```

**Mac OS:** `shasum -a 1 bitgreen-airdrop-verifier-macos.zip`
```
52f9cebf40e8ba264a0becf3652053d8558e13b6 bitgreen-airdrop-verifier-macos.zip
```

**Linux:** `sha1sum bitgreen-airdrop-verifier-linux.zip`
```
dd807d6649ce0ba030f67dbcf878113c6de545a2 bitgreen-airdrop-verifier-linux.zip
```

---


### Prerequisites
[Python 3.8.5](https://www.python.org/downloads/release/python-385/)

##### Windows
`pip3 install bsddb3-6.2.9-cp38-cp38-win_amd64.whl` https://www.lfd.uci.edu/~gohlke/pythonlibs/#bsddb3  
`pip3 install -r requirements.txt`

#### Mac OS
`brew install berkeley-db@4`  
`BERKELEYDB_DIR=$(brew --prefix berkeley-db@4) pip3 install bsddb3`  
`python3 -m easy_install bsddb3`  
`pip3 install -r requirements.txt`

##### __Ubuntu 20.04+__
`sudo apt install python3-pip python3-tk python3-pil.imagetk`  
`pip3 install -r requirements.txt`

## Setup .env
Copy `.env.example` to `.env` and edit env variables.

### Local testing
When testing locally, move contents inside /img into the root folder of main.py before invoking `python3 main.py` or `py .\main.py` for windows user.

### PyInstaller - building standalone application (Windows, Linux, Mac OS)
Windows:  
```pyinstaller --onefile main.py --add-data "img\*.jpg;." --add-data "img\*.gif;." --add-data "img\*.ico;." --add-data ".env;." --noconsole --icon=img\favicon.ico --add-data="coincurve\*.dll;coincurve/"  -n bitgreen-airdrop-verifier --clean```  

Ubuntu:  
```pyinstaller --onefile main.py --add-data "img/*.jpg:." --add-data "img/*.gif:." --add-data ".env:." --noconsole -n bitgreen-airdrop-verifier --clean --hidden-import='PIL._tkinter_finder'```

Mac OS:  
```python3 -m PyInstaller --onefile main.py --add-data "img/*.jpg:." --add-data "img/*.gif:." --add-data "img/*.ico:." --add-data ".env:." --noconsole --icon=img/favicon.ico -n bitgreen-airdrop-verifier --clean --codesign-identity="IDENTITY"```