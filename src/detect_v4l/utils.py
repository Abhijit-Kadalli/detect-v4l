import subprocess
import os
import platform
import re
from typing import Dict, List, Tuple, Optional, Any

def is_linux() -> bool:
    """Check if the current operating system is Linux"""
    return platform.system() == "Linux"

def command_exists(command: str) -> bool:
    """Check if a command exists in the system PATH"""
    return subprocess.run(
        ["which", command], 
        capture_output=True, 
        text=True
    ).returncode == 0

def get_linux_distribution() -> Tuple[str, str]:
    """
    Get the Linux distribution name and version
    
    Returns:
        Tuple of (distro_name, distro_version)
    """
    distro = ""
    version = ""
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    distro = line.split("=")[1].strip().strip('"')
                elif line.startswith("VERSION_ID="):
                    version = line.split("=")[1].strip().strip('"')
    except:
        pass
    return distro, version

def get_installation_command(package_name: str) -> str:
    """
    Get the appropriate installation command for the current distribution
    
    Args:
        package_name: Name of the package to install
        
    Returns:
        Installation command string
    """
    distro, _ = get_linux_distribution()
    
    if distro in ["ubuntu", "debian", "linuxmint"]:
        return f"sudo apt install {package_name}"
    elif distro in ["fedora", "rhel", "centos"]:
        return f"sudo dnf install {package_name}"
    elif distro == "arch":
        return f"sudo pacman -S {package_name}"
    elif distro in ["opensuse", "suse"]:
        return f"sudo zypper install {package_name}"
    else:
        return f"Please install the {package_name} package using your distribution's package manager"

def parse_device_capabilities(device_path: str) -> Dict[str, Any]:
    """
    Parse device capabilities using v4l2-ctl
    
    Args:
        device_path: Path to the video device (e.g., /dev/video0)
        
    Returns:
        Dictionary of device capabilities
    """
    if not is_linux() or not command_exists("v4l2-ctl"):
        return {}
        
    try:
        result = subprocess.run(
            ["v4l2-ctl", "--device", device_path, "--all"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {}
            
        caps = {}
        
        # Parse driver info
        driver_match = re.search(r"Driver name\s+:\s+(.+)", result.stdout)
        if driver_match:
            caps["driver"] = driver_match.group(1)
            
        # Parse device info
        card_match = re.search(r"Card type\s+:\s+(.+)", result.stdout)
        if card_match:
            caps["name"] = card_match.group(1)
            
        # Parse supported formats
        formats = []
        format_section = re.search(r"Format Video Capture:([\s\S]+?)Priority:", result.stdout)
        if format_section:
            format_text = format_section.group(1)
            format_matches = re.finditer(r"[^\S\n\r]+\d+:\s+([A-Z0-9_]+)\s+\d+x\d+", format_text)
            for match in format_matches:
                formats.append(match.group(1))
        caps["formats"] = formats
        
        # Parse supported resolutions
        resolutions = []
        size_matches = re.finditer(r"Size: Discrete (\d+x\d+)", result.stdout)
        for match in size_matches:
            resolutions.append(match.group(1))
        caps["resolutions"] = resolutions
        
        return caps
    except Exception as e:
        print(f"Error parsing device capabilities: {str(e)}")
        return {}

def is_device_ready(device_path: str) -> bool:
    """
    Check if a video device is ready for use
    
    Args:
        device_path: Path to the video device
        
    Returns:
        True if the device is ready, False otherwise
    """
    if not os.path.exists(device_path):
        return False
        
    try:
        # Try to open the device for reading
        with open(device_path, "rb") as f:
            # Just testing if we can open it
            pass
        return True
    except:
        return False