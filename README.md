

## Requirements

### Operating Systems

- Windows 10/11


### ensure echowaveII is installed with driveres


# STEP1 virtual environment

```bash setup
py 3.12 -m venv ct_pipeline
.\ct_pipeline\Scripts\Activate.ps1

```

# STEP 2  run cmds
```bash run 
python feeder.py  
```
# if modules doesn't exist
```bash
pip3 install opencv-python numpy  # don't install if already did pip install -r requirements.txt in CT_Cloud, as it is already installed
```

# STEP3 open cmd-prompt as administrator
```bash run as administrator
python -m pip install pywin32
pip install pyautogui
python command_rx.py   # go to directory first 
```

