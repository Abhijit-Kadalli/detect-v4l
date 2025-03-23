import pytest
from unittest.mock import patch, MagicMock
import subprocess
import platform
import os

from detect_v4l.detector import CameraDetector
from detect_v4l.utils import is_linux, command_exists


class TestCameraDetector:
    
    @patch('detect_v4l.detector.is_linux')
    @patch('detect_v4l.detector.command_exists')
    def test_check_dependencies_success(self, mock_command_exists, mock_is_linux):
        # Setup mocks
        mock_is_linux.return_value = True
        mock_command_exists.return_value = True
        
        # Call method
        satisfied, message = CameraDetector.check_dependencies()
        
        # Check results
        assert satisfied is True
        assert "All dependencies satisfied" in message
        mock_is_linux.assert_called_once()
        mock_command_exists.assert_called_once_with("v4l2-ctl")
    
    @patch('detect_v4l.detector.is_linux')
    def test_check_dependencies_not_linux(self, mock_is_linux):
        # Setup mocks
        mock_is_linux.return_value = False
        
        # Call method
        satisfied, message = CameraDetector.check_dependencies()
        
        # Check results
        assert satisfied is False
        assert "only works on Linux" in message
        mock_is_linux.assert_called_once()
    
    @patch('detect_v4l.detector.is_linux')
    @patch('detect_v4l.detector.command_exists')
    @patch('detect_v4l.detector.get_installation_command')
    def test_check_dependencies_missing_v4l2(self, mock_get_cmd, mock_command_exists, mock_is_linux):
        # Setup mocks
        mock_is_linux.return_value = True
        mock_command_exists.return_value = False
        mock_get_cmd.return_value = "sudo apt install v4l-utils"
        
        # Call method
        satisfied, message = CameraDetector.check_dependencies()
        
        # Check results
        assert satisfied is False
        assert "Missing dependency" in message
        assert "v4l2-ctl not found" in message
        mock_is_linux.assert_called_once()
        mock_command_exists.assert_called_once_with("v4l2-ctl")
        mock_get_cmd.assert_called_once_with("v4l-utils")
    
    @patch('detect_v4l.detector.CameraDetector.check_dependencies')
    @patch('subprocess.run')
    @patch('detect_v4l.detector.is_device_ready')
    def test_list_cameras_success(self, mock_is_ready, mock_subprocess, mock_check_deps):
        # Setup mocks
        mock_check_deps.return_value = (True, "All dependencies satisfied")
        mock_is_ready.return_value = True
        
        # Mock the v4l2-ctl output
        v4l2_output = "Camera 1 (usb-0000:00:14.0-1):\n\t/dev/video0\n\n" + \
                      "Camera 2 (usb-0000:00:14.0-2):\n\t/dev/video1\n\n"
        
        # Mock the udevadm output for two cameras
        udev_output1 = "ID_VENDOR_ID=046d\nID_MODEL_ID=0825\n"
        udev_output2 = "ID_VENDOR_ID=04f2\nID_MODEL_ID=b68b\n"
        
        # Create CompletedProcess objects directly
        v4l2_result = MagicMock()
        v4l2_result.stdout = v4l2_output
        v4l2_result.returncode = 0
        
        udev_result1 = MagicMock()
        udev_result1.stdout = udev_output1
        udev_result1.returncode = 0
        
        udev_result2 = MagicMock()
        udev_result2.stdout = udev_output2
        udev_result2.returncode = 0
        
        # Configure subprocess.run to return the appropriate objects
        def side_effect(cmd, **kwargs):
            if cmd[0] == 'v4l2-ctl' and cmd[1] == '--list-devices':
                return v4l2_result
            elif cmd[0] == 'udevadm':
                if cmd[3] == '/dev/video0':
                    return udev_result1
                elif cmd[3] == '/dev/video1':
                    return udev_result2
            return MagicMock(stdout="", returncode=1)
        
        mock_subprocess.side_effect = side_effect
        
        # Call method
        cameras = CameraDetector.list_cameras()
        print(cameras)
        
        # Check results
        assert len(cameras) == 2
        assert cameras[('046d', '0825')] == 0
        assert cameras[('04f2', 'b68b')] == 1
        mock_check_deps.assert_called_once()
        assert mock_subprocess.call_count == 3  # One for v4l2-ctl and two for udevadm
    
    @patch('detect_v4l.detector.CameraDetector.check_dependencies')
    def test_list_cameras_dependencies_not_met(self, mock_check_deps):
        # Setup mocks
        mock_check_deps.return_value = (False, "Missing dependencies")
        
        # Call method
        cameras = CameraDetector.list_cameras()
        
        # Check results
        assert cameras == {}
        mock_check_deps.assert_called_once()
    
    @patch('detect_v4l.detector.CameraDetector.list_cameras')
    def test_find_camera_by_vendor_model_found(self, mock_list_cameras):
        # Setup mocks
        mock_list_cameras.return_value = {
            ('046d', '0825'): 0,
            ('04f2', 'b68b'): 1
        }
        
        # Call method
        device_number = CameraDetector.find_camera_by_vendor_model('046d', '0825')
        
        # Check results
        assert device_number == 0
        mock_list_cameras.assert_called_once()
    
    @patch('detect_v4l.detector.CameraDetector.list_cameras')
    def test_find_camera_by_vendor_model_not_found(self, mock_list_cameras):
        # Setup mocks
        mock_list_cameras.return_value = {
            ('046d', '0825'): 0,
            ('04f2', 'b68b'): 1
        }
        
        # Call method
        device_number = CameraDetector.find_camera_by_vendor_model('1234', '5678')
        
        # Check results
        assert device_number is None
        mock_list_cameras.assert_called_once()
    
    @patch('detect_v4l.detector.CameraDetector.list_cameras')
    def test_find_cameras_by_vendor_model_list(self, mock_list_cameras):
        # Setup mocks
        mock_list_cameras.return_value = {
            ('046d', '0825'): 0,
            ('04f2', 'b68b'): 1,
            ('1234', '5678'): 2
        }
        
        # Call method
        vendor_model_list = [('046d', '0825'), ('1234', '5678'), ('9999', '9999')]
        device_numbers = CameraDetector.find_cameras_by_vendor_model_list(vendor_model_list)
        
        # Check results
        assert device_numbers == [0, 2]
        mock_list_cameras.assert_called_once()
