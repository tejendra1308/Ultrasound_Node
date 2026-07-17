# Ultrasound_Node

Streams a captured window (MicrUs/Echo Wave II) to a Quest 3 over TCP, and
receives control commands from the Quest 3 over UDP and replays them as
keypresses into the app.

## Architecture

```
config/
  settings.py              defaults + loader (merges settings.local.json over them)
  settings.local.json.example   copy to settings.local.json to override anything
  commands.json             command name -> key sequence (pure data)

core/
  window_capture.py         WindowCapture: find a window, grab a cropped/resized frame
  video_stream.py           VideoStreamServer: generic TCP JPEG streamer (any frame source)
  input_backend.py          InputBackend: "focus window, press keys" — windows/dummy impls
  command_dispatch.py       CommandDispatcher: command name -> key sequence -> backend
  discovery.py              ServiceBroadcaster: multicast discovery for Unity

feeder.py       entry point: WindowCapture -> VideoStreamServer -> ServiceBroadcaster
command_rx.py   entry point: commands.json -> CommandDispatcher -> InputBackend
```


## Requirements

- Windows 10/11 (for real capture/input — `core/window_capture.py` and the
  `windows` input backend use `win32gui`/`pyautogui`)
- Echo Wave II installed with drivers

## Setup

```bash
python -m venv ct_pipeline
.\ct_pipeline\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy the example override file and set your input backend to real hardware:

```bash
copy config\settings.local.json.example config\settings.local.json
```

Edit `config/settings.local.json` and set `"input_backend": "windows"`.


## Run

Terminal 1 — video feeder:
```bash
python feeder.py
```

Terminal 2 — command receiver (run as Administrator on Windows, so it can
send keystrokes to other applications):
```bash
python -m pip install pywin32 pyautogui
python command_rx.py
```

# packages needed
```bash
pip3 install opencv-python numpy
```



If `feeder.py` can't find your window, it prints every visible window title
— copy the right one into `window.title_hint` in your local settings.



## Common changes, and where they go

| I want to...                              | Edit this, nothing else                          |
|--------------------------------------------|----------------------------------------------------|
| Add a new UDP command                      | `config/commands.json`                              |
| Change ports, FPS, JPEG quality, crop box  | `config/settings.local.json` (copy the `.example`) |
| Point at a different app window            | `window.title_hint` in your local settings         |
| Test command logic on macOS/Linux          | `command.input_backend: "dummy"` (default)          |
| Deliver keys a different way (not pyautogui)| new class in `core/input_backend.py`               |
| Stream a different frame source            | pass a different `frame_provider` to `VideoStreamServer` in `feeder.py` |
| Add a second node (different app/window)   | copy `feeder.py`/`command_rx.py`, point at a different `config/settings.local.json` |

No file above requires touching more than one place to make a change —
config and code are separated so growing the command set or adding a new
capture target doesn't mean editing the streaming or discovery logic.
