import subprocess
import re
from typing import Dict, List, Tuple, Optional, Any
from .utils import is_linux, command_exists, get_installation_command, parse_device_capabilities, is_device_ready


class CameraDetector:
    """A class to detect and identify V4L cameras connected to the system"""

    @staticmethod
    def check_dependencies() -> Tuple[bool, str]:
        """
        Check if required dependencies are installed
        
        Returns:
            Tuple of (is_satisfied, message)
        """
        # First check if running on Linux
        if not is_linux():
            return False, "This library only works on Linux systems with V4L support"
        
        # Check for v4l2-ctl
        if not command_exists("v4l2-ctl"):
            install_cmd = get_installation_command("v4l-utils")
            return False, f"Missing dependency: v4l2-ctl not found.\nPlease install the v4l-utils package:\n{install_cmd}"
        
        return True, "All dependencies satisfied"
    
    @staticmethod
    def list_cameras() -> Dict[Tuple[str, str], int]:
        """
        List all connected cameras with their vendor and model IDs
        
        Returns:
            Dictionary mapping (vendor_id, model_id) to device number
        """
        
        # Check if dependencies are satisfied
        deps_satisfied, msg = CameraDetector.check_dependencies()
        if not deps_satisfied:
            print(f"Error: {msg}")
            return {}
        
        try:
            # List video devices
            result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                                    capture_output=True, text=True)
            devices = result.stdout.strip().split('\n\n')

            cameras = {}

            for device in devices:
                if device:
                    lines = device.split('\n')
                    device_name = lines[0].strip()
                    device_paths = [line.strip() for line in lines[1:] if '/dev/' in line]

                    if device_paths:
                        video_path = device_paths[0]
                        video_match = re.search(r'/dev/video(\d+)', video_path)
                        
                        if video_match and is_device_ready(video_path):
                            device_number = int(video_match.group(1))

                            # Get Vendor & Model ID using `udevadm`
                            udev_result = subprocess.run(
                                ['udevadm', 'info', '--query=all', '--name', video_path],
                                capture_output=True, text=True
                            )
                            
                            vendor_match = re.search(r'ID_VENDOR_ID=(\w+)', udev_result.stdout)
                            model_match = re.search(r'ID_MODEL_ID=(\w+)', udev_result.stdout)

                            if vendor_match and model_match:
                                vendor_id = vendor_match.group(1)
                                model_id = model_match.group(1)
                                cameras[(vendor_id, model_id)] = device_number
                                print(f"Detected Camera: {device_name} | Vendor: {vendor_id} | Model: {model_id} | Device: {device_number}")

            return cameras
        except Exception as e:
            print(f"Error detecting cameras: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    @staticmethod
    def find_camera_by_vendor_model(vendor_id: str, model_id: str) -> Optional[int]:
        """
        Find a specific camera by its vendor and model ID
        
        Args:
            vendor_id: Vendor ID of the camera
            model_id: Model ID of the camera
            
        Returns:
            Device number if found, None otherwise
        """
        cameras = CameraDetector.list_cameras()
        camera_key = (vendor_id, model_id)
        return cameras.get(camera_key)
    
    @staticmethod
    def find_cameras_by_vendor_model_list(vendor_model_list: List[Tuple[str, str]]) -> List[int]:
        """
        Find multiple cameras by a list of vendor and model IDs
        
        Args:
            vendor_model_list: List of (vendor_id, model_id) tuples
            
        Returns:
            List of device numbers for the found cameras
        """
        cameras = CameraDetector.list_cameras()
        result = []
        
        for vendor_model in vendor_model_list:
            if vendor_model in cameras:
                result.append(cameras[vendor_model])
                
        return result
    
    @staticmethod
    def get_camera_capabilities(device_number: int) -> Dict[str, Any]:
        """
        Get detailed capabilities of a camera device
        
        Args:
            device_number: Device number (e.g., 0 for /dev/video0)
            
        Returns:
            Dictionary containing device capabilities information
        """
        device_path = f"/dev/video{device_number}"
        return parse_device_capabilities(device_path)