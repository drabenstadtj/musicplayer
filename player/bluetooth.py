"""Bluetooth audio management for Raspberry Pi"""
import subprocess
import re


class BluetoothManager:
    """Manage Bluetooth audio connections on Raspberry Pi"""

    def __init__(self):
        self.bluetoothctl_available = self._check_bluetoothctl()

    def _check_bluetoothctl(self):
        """Check if bluetoothctl is available"""
        try:
            subprocess.run(['bluetoothctl', '--version'],
                         capture_output=True,
                         check=True,
                         timeout=2)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _run_bluetoothctl(self, command, timeout=5):
        """Run a bluetoothctl command"""
        try:
            result = subprocess.run(
                ['bluetoothctl'] + command.split(),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout
        except Exception as e:
            return f"Error: {e}"

    def scan_devices(self, duration=5):
        """Scan for nearby Bluetooth devices

        Returns:
            List of tuples (mac_address, device_name, paired_status)
        """
        if not self.bluetoothctl_available:
            return []

        devices = []

        try:
            # Start scanning
            subprocess.Popen(['bluetoothctl', 'scan', 'on'],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)

            # Wait for scan
            import time
            time.sleep(duration)

            # Stop scanning
            subprocess.run(['bluetoothctl', 'scan', 'off'],
                         capture_output=True,
                         timeout=2)

            # Get list of devices
            result = subprocess.run(['bluetoothctl', 'devices'],
                                  capture_output=True,
                                  text=True,
                                  timeout=2)

            # Parse devices
            # Format: "Device XX:XX:XX:XX:XX:XX Device Name"
            for line in result.stdout.split('\n'):
                match = re.match(r'Device\s+([0-9A-F:]+)\s+(.+)', line)
                if match:
                    mac = match.group(1)
                    name = match.group(2)
                    paired = self.is_paired(mac)
                    devices.append((mac, name, paired))

        except Exception as e:
            pass

        return devices

    def is_paired(self, mac_address):
        """Check if device is paired"""
        try:
            result = subprocess.run(
                ['bluetoothctl', 'info', mac_address],
                capture_output=True,
                text=True,
                timeout=2
            )
            return 'Paired: yes' in result.stdout
        except:
            return False

    def is_connected(self, mac_address):
        """Check if device is connected"""
        try:
            result = subprocess.run(
                ['bluetoothctl', 'info', mac_address],
                capture_output=True,
                text=True,
                timeout=2
            )
            return 'Connected: yes' in result.stdout
        except:
            return False

    def pair_device(self, mac_address):
        """Pair with a device"""
        try:
            result = subprocess.run(
                ['bluetoothctl', 'pair', mac_address],
                capture_output=True,
                text=True,
                timeout=30
            )
            return 'Pairing successful' in result.stdout or 'already paired' in result.stdout
        except Exception as e:
            return False

    def trust_device(self, mac_address):
        """Trust a device (auto-connect)"""
        try:
            subprocess.run(
                ['bluetoothctl', 'trust', mac_address],
                capture_output=True,
                timeout=5
            )
            return True
        except:
            return False

    def connect_device(self, mac_address):
        """Connect to a paired device"""
        try:
            result = subprocess.run(
                ['bluetoothctl', 'connect', mac_address],
                capture_output=True,
                text=True,
                timeout=30
            )
            success = 'Connection successful' in result.stdout or 'already connected' in result.stdout

            if success:
                # Trust device for auto-reconnect
                self.trust_device(mac_address)

            return success
        except Exception as e:
            return False

    def disconnect_device(self, mac_address):
        """Disconnect from a device"""
        try:
            subprocess.run(
                ['bluetoothctl', 'disconnect', mac_address],
                capture_output=True,
                timeout=5
            )
            return True
        except:
            return False

    def remove_device(self, mac_address):
        """Remove/unpair a device"""
        try:
            subprocess.run(
                ['bluetoothctl', 'remove', mac_address],
                capture_output=True,
                timeout=5
            )
            return True
        except:
            return False

    def get_connected_devices(self):
        """Get list of currently connected devices

        Returns:
            List of tuples (mac_address, device_name)
        """
        devices = []
        try:
            result = subprocess.run(
                ['bluetoothctl', 'devices'],
                capture_output=True,
                text=True,
                timeout=2
            )

            for line in result.stdout.split('\n'):
                match = re.match(r'Device\s+([0-9A-F:]+)\s+(.+)', line)
                if match:
                    mac = match.group(1)
                    name = match.group(2)
                    if self.is_connected(mac):
                        devices.append((mac, name))

        except:
            pass

        return devices

    def set_as_default_sink(self):
        """Set Bluetooth as default audio sink using PulseAudio"""
        try:
            # List sinks and find bluez (Bluetooth) sink
            result = subprocess.run(
                ['pactl', 'list', 'short', 'sinks'],
                capture_output=True,
                text=True,
                timeout=2
            )

            # Find bluez sink
            for line in result.stdout.split('\n'):
                if 'bluez' in line.lower():
                    sink_name = line.split()[1]
                    # Set as default
                    subprocess.run(
                        ['pactl', 'set-default-sink', sink_name],
                        timeout=2
                    )
                    return True

        except Exception as e:
            pass

        return False
