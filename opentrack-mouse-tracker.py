#!/usr/bin/env python3
"""
OpenTrack Calibrated Mouse Control with Toggle
Can be enabled/disabled via external commands
"""

import socket
import struct
import subprocess
import time
import signal
import sys
import os
import json

# OpenTrack UDP protocol
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

# Control
enabled = True
recalibrate_requested = False

# Calibration file
CONFIG_DIR = os.path.expanduser('~/.config/headmouse')
CALIBRATION_FILE = os.path.join(CONFIG_DIR, 'calibration.json')

def get_screen_size():
    """Get screen resolution"""
    try:
        result = subprocess.run(['xdpyinfo'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'dimensions:' in line:
                dims = line.split()[1]
                width, height = dims.split('x')
                return int(width), int(height)
    except Exception as e:
        print(f"Error getting screen size: {e}")
    return 1920, 1080

def move_mouse_absolute(x, y):
    """Move mouse cursor to absolute position"""
    try:
        subprocess.run(['xdotool', 'mousemove', str(int(x)), str(int(y))],
                      check=False, capture_output=True)
    except Exception as e:
        pass

def collect_samples(sock, duration=2.0):
    """Collect samples for duration"""
    samples = []
    start_time = time.time()
    sock.settimeout(0.01)

    while time.time() - start_time < duration:
        try:
            data, addr = sock.recvfrom(48)
            if len(data) == 48:
                values = struct.unpack('dddddd', data)
                x, y, z, yaw, pitch, roll = values
                samples.append({'yaw': yaw, 'pitch': pitch})
        except socket.timeout:
            continue

    return samples

def save_calibration(calibration):
    """Save calibration to file"""
    try:
        # Create config directory if it doesn't exist
        os.makedirs(CONFIG_DIR, exist_ok=True)

        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(calibration, f)
        print(f"✓ Calibration saved to {CALIBRATION_FILE}")
        return True
    except Exception as e:
        print(f"Error saving calibration: {e}")
        return False

def load_calibration():
    """Load calibration from file"""
    try:
        if os.path.exists(CALIBRATION_FILE):
            with open(CALIBRATION_FILE, 'r') as f:
                calibration = json.load(f)
            print(f"✓ Loaded calibration from {CALIBRATION_FILE}")
            print(f"Center: yaw={calibration['center_yaw']:+.1f}°, pitch={calibration['center_pitch']:+.1f}°")
            print(f"Yaw range: ±{calibration['yaw_range']:.1f}°")
            print(f"Pitch range: ±{calibration['pitch_range']:.1f}°")
            print()
            return calibration
    except Exception as e:
        print(f"Error loading calibration: {e}")
    return None

def calibrate(sock):
    """Calibrate based on extreme positions"""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║           CALIBRATION - 5 Steps                            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    positions = {}

    steps = [
        ('center', 'Look at the CENTER of your screen'),
        ('top_left', 'Look at the TOP LEFT corner'),
        ('top_right', 'Look at the TOP RIGHT corner'),
        ('bottom_left', 'Look at the BOTTOM LEFT corner'),
        ('bottom_right', 'Look at the BOTTOM RIGHT corner'),
    ]

    for pos_name, instruction in steps:
        print(f"Step: {instruction}")
        if sys.stdin.isatty():
            input("Press ENTER when ready, then hold your gaze for 2 seconds...")
        else:
            print("Starting in 3 seconds...")
            time.sleep(3)

        samples = collect_samples(sock, duration=2.0)

        if len(samples) == 0:
            print("ERROR: No data from OpenTrack!")
            return None

        avg_yaw = sum(s['yaw'] for s in samples) / len(samples)
        avg_pitch = sum(s['pitch'] for s in samples) / len(samples)

        positions[pos_name] = {'yaw': avg_yaw, 'pitch': avg_pitch}
        print(f"✓ Recorded: yaw={avg_yaw:+.1f}°, pitch={avg_pitch:+.1f}°")
        print()

    # Calculate ranges
    center_yaw = positions['center']['yaw']
    center_pitch = positions['center']['pitch']

    yaw_left = abs(positions['top_left']['yaw'] - center_yaw)
    yaw_right = abs(positions['top_right']['yaw'] - center_yaw)
    yaw_range = max(yaw_left, yaw_right)

    pitch_up = abs(positions['top_left']['pitch'] - center_pitch)
    pitch_down = abs(positions['bottom_left']['pitch'] - center_pitch)
    pitch_range = max(pitch_up, pitch_down)

    print("Calibration complete!")
    print(f"Center: yaw={center_yaw:+.1f}°, pitch={center_pitch:+.1f}°")
    print(f"Yaw range: ±{yaw_range:.1f}°")
    print(f"Pitch range: ±{pitch_range:.1f}°")
    print()

    calibration = {
        'center_yaw': center_yaw,
        'center_pitch': center_pitch,
        'yaw_range': yaw_range,
        'pitch_range': pitch_range
    }

    save_calibration(calibration)

    return calibration

def map_to_screen(yaw, pitch, screen_width, screen_height, calibration):
    """Map head position to screen coordinates using calibration"""
    center_yaw = calibration['center_yaw']
    center_pitch = calibration['center_pitch']
    yaw_range = calibration['yaw_range']
    pitch_range = calibration['pitch_range']

    rel_yaw = yaw - center_yaw
    rel_pitch = pitch - center_pitch

    rel_yaw = max(-yaw_range, min(yaw_range, rel_yaw))
    rel_pitch = max(-pitch_range, min(pitch_range, rel_pitch))

    norm_x = (rel_yaw + yaw_range) / (2 * yaw_range)
    norm_y = (rel_pitch + pitch_range) / (2 * pitch_range)

    norm_y = 1.0 - norm_y

    x = norm_x * screen_width
    y = norm_y * screen_height

    return x, y

def handle_sigusr1(signum, frame):
    """Toggle on SIGUSR1"""
    global enabled
    enabled = not enabled
    status = "ENABLED" if enabled else "DISABLED"
    print(f"\nHead tracking: {status}")

def handle_sigusr2(signum, frame):
    """Recalibrate on SIGUSR2"""
    global recalibrate_requested
    recalibrate_requested = True
    print(f"\nRecalibration requested...")

def main():
    global enabled, recalibrate_requested

    # Set up signal handlers
    signal.signal(signal.SIGUSR1, handle_sigusr1)
    signal.signal(signal.SIGUSR2, handle_sigusr2)

    screen_width, screen_height = get_screen_size()
    print(f"Screen: {screen_width}x{screen_height}")
    print()

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    # Try to load existing calibration
    calibration = load_calibration()

    # If no calibration exists, run calibration
    if not calibration:
        print("No saved calibration found. Starting calibration...")
        print()
        calibration = calibrate(sock)
        if not calibration:
            return

    # Write PID to file for control script
    with open('/tmp/opentrack_mouse.pid', 'w') as f:
        f.write(str(sys.argv[0]))  # Write script name
        f.write('\n')
        f.write(str(os.getpid()))  # Write PID

    print("Control commands:")
    print("  Toggle tracking: opentrack-mouse toggle")
    print("  Recalibrate:     opentrack-mouse calibrate")
    print()
    # Check if we're running interactively (has a terminal)
    if sys.stdin.isatty():
        input("Press ENTER to start mouse control...")
    print()
    print("Running... Move your head to control the mouse!")
    print("Press Ctrl+C to exit")
    print()

    # Main loop
    sock.settimeout(0.01)
    while True:
        try:
            # Check if recalibration requested
            if recalibrate_requested:
                recalibrate_requested = False
                print("\n" + "="*60)
                print("RECALIBRATING...")
                print("="*60 + "\n")
                new_calibration = calibrate(sock)
                if new_calibration:
                    calibration = new_calibration
                    print("\n✓ Recalibration complete! Resuming tracking...")
                    print()
                else:
                    print("\n❌ Recalibration failed! Using old calibration...")
                    print()

            data, addr = sock.recvfrom(48)

            if len(data) == 48:
                values = struct.unpack('dddddd', data)
                x, y, z, yaw, pitch, roll = values

                # Only move mouse if enabled
                if enabled:
                    mouse_x, mouse_y = map_to_screen(yaw, pitch, screen_width, screen_height, calibration)
                    move_mouse_absolute(mouse_x, mouse_y)

        except socket.timeout:
            continue
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()
