# detect_v4l

A Python library for detecting and identifying Video4Linux (V4L) cameras on Linux systems.

## Installation

```bash
pip install detect_v4l
```

## Usage

```python
from detect_v4l import CameraDetector

# List all connected cameras
cameras = CameraDetector.list_cameras()
print(cameras)  # {('046d', '0825'): 0, ('04f2', 'b68b'): 1}

# Find a specific camera
device_number = CameraDetector.find_camera_by_vendor_model('046d', '0825')
print(f"Found camera at /dev/video{device_number}")

# Find multiple cameras from a list
device_numbers = CameraDetector.find_cameras_by_vendor_model_list([
    ('046d', '0825'),
    ('04f2', 'b68b')
])
print(f"Found cameras at: {[f'/dev/video{num}' for num in device_numbers]}")
```

## Requirements

- Linux system with V4L support
- v4l2-ctl command-line tool
- Python 3.6+

## License

MIT
