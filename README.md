Temporary notes on building for various platforms. More information to be added as progress/testing is carried out.

### prerequisites
[Python 3.8.5](https://www.python.org/downloads/release/python-385/)  
pip3 install requests pillow tkmacosx

### Local testing
When testing locally, move contents inside /img into the root folder of main.py before invoking `python3 main.py` or `py .\main.py` for windows user.

### pyinstaller - building standalone application (Windows, Linux, Mac OS)
Windows:  
```pyinstaller --onefile main.py --add-data "img\*.jpg;." --add-data "img\*.ico;." --noconsole --icon=img\favicon.ico -n bitgreen-swap-tool --clean``` 

Mac OS:  ```pyinstaller```
