### Checking application authenticity
Always check authenticity of any application you are downloading. By utilizing the following commands, you are ensuring the application you have downloaded hasn't been modified and should match the values below.

Windows: `certutil -hashfile bitgreen-swap-tool.exe`
```
SHA1 hash of bitgreen-swap-tool.exe:
01d93a3d26bd9c0ada23ae299495278ae18d16cc
CertUtil: -hashfile command completed successfully.
```

Mac OS: `shasum -a 1 bitgreen-swap-tool`
```

```



### prerequisites
[Python 3.8.5](https://www.python.org/downloads/release/python-385/)  
pip3 install requests pillow tkmacosx

### Local testing
When testing locally, move contents inside /img into the root folder of main.py before invoking `python3 main.py` or `py .\main.py` for windows user.

### pyinstaller - building standalone application (Windows, Linux, Mac OS)
Windows:  
```pyinstaller --onefile main.py --add-data "img\*.jpg;." --add-data "img\*.ico;." --noconsole --icon=img\favicon.ico -n bitgreen-swap-tool --clean``` 

Mac OS:  ```pyinstaller```
