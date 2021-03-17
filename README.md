Temporary notes on building for various platforms. More information to be added as progress/testing is carried out.

### pyinstaller - building standalone application (Windows, Linux, Mac OS)
Windows:  
```pyinstaller --onefile main.py --add-data "img\*.jpg;." --add-data "img\*.ico;." --noconsole --icon=img\favicon.ico -n bitgreen-swap-tool --clean```

Linux:   ```pyinstaller```   

Mac OS:  ```pyinstaller```
