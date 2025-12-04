# Complete Installation Guide for HeadMouse

This guide covers everything needed to set up head tracking mouse control from scratch on a fresh Debian/Ubuntu system.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installing OpenTrack](#installing-opentrack)
3. [Installing HeadMouse Scripts](#installing-headmouse-scripts)
4. [OpenTrack Configuration](#opentrack-configuration)
5. [Testing & Calibration](#testing--calibration)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

- **OS**: Debian 12+ / Ubuntu 20.04+
- **Hardware**: Webcam (built-in or USB)
- **Optional**: Proper head tracking hardware (TrackIR, etc.) for better accuracy
- **Desktop**: Any (tested with i3wm)

---

## Installing OpenTrack

OpenTrack needs to be built from source with ONNX Runtime support for the NeuralNet face tracker.

### Step 1: Build ONNX Runtime 1.21

OpenTrack's NeuralNet tracker requires ONNX Runtime 1.21+, which isn't available in Debian repos.

```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install -y build-essential cmake git wget python3 python3-pip \
    libprotobuf-dev protobuf-compiler

# Clone ONNX Runtime
cd /tmp
git clone --recursive --branch v1.21.0 https://github.com/microsoft/onnxruntime.git
cd onnxruntime

# Fix Eigen hash mismatch (known issue)
# Edit cmake/deps.txt line 25 and change the Eigen SHA1 hash:
# From: 5ea4d05e62d7f954a46b3213f9b2535bdd866803
# To:   51982be81bbe52572b54180454df11a3ece9a934
sed -i 's/5ea4d05e62d7f954a46b3213f9b2535bdd866803/51982be81bbe52572b54180454df11a3ece9a934/' cmake/deps.txt

# Build ONNX Runtime (takes 30-60 minutes)
./build.sh --config Release --build_shared_lib --parallel --skip_tests \
    --cmake_extra_defines CMAKE_INSTALL_PREFIX=/usr/local

# Install to system
cd build/Linux/Release
sudo make install
sudo ldconfig
```

**Verify ONNX Runtime installation:**
```bash
ls /usr/local/lib/libonnxruntime.so*
# Should show: /usr/local/lib/libonnxruntime.so.1.21.0
```

### Step 2: Build OpenTrack

```bash
# Install OpenTrack dependencies
sudo apt-get install -y qtbase5-dev qttools5-dev libopencv-dev \
    libprocps-dev git cmake

# Clone OpenTrack
cd /tmp
git clone https://github.com/opentrack/opentrack.git
cd opentrack

# Create build directory
mkdir -p build
cd build

# Configure with ONNX Runtime support
cmake .. -DCMAKE_BUILD_TYPE=Release \
    -DONNXRUNTIME_INCLUDE_DIR=/usr/local/include/onnxruntime \
    -DONNXRUNTIME_LIBRARY=/usr/local/lib/libonnxruntime.so

# Build (takes 10-20 minutes)
make -j$(nproc)

# Install to system
sudo make install

# Set library path for runtime
echo 'export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

**Verify OpenTrack installation:**
```bash
which opentrack
# Should show: /usr/local/bin/opentrack

opentrack --version
# Should start without errors (close it after testing)
```

### Step 3: Download Neural Network Models

OpenTrack's NeuralNet tracker requires model files:

```bash
# Models are typically included in the OpenTrack repo
# If missing, download from:
cd /tmp/opentrack
ls contrib/

# Models should be at:
# - contrib/head-localizer.onnx
# - contrib/head-pose.onnx (or variants)

# They're automatically installed during 'make install'
# Verify installation:
ls /usr/local/share/opentrack/
```

---

## Installing HeadMouse Scripts

### Method 1: From GitHub (Recommended)

```bash
# Clone the repository
cd ~
git clone https://github.com/lawless-m/HeadMouse.git
cd HeadMouse

# Install scripts
sudo cp opentrack-mouse-tracker.py /usr/local/bin/opentrack-mouse-tracker
sudo cp opentrack-mouse /usr/local/bin/opentrack-mouse
sudo chmod +x /usr/local/bin/opentrack-mouse-tracker
sudo chmod +x /usr/local/bin/opentrack-mouse

# Install Python dependencies
sudo apt-get install -y python3 xdotool x11-utils
```

### Method 2: Manual Installation

Download the two files from the GitHub repo:
- `opentrack-mouse-tracker.py`
- `opentrack-mouse`

Then install as above.

---

## OpenTrack Configuration

### Initial Setup

1. **Start OpenTrack:**
   ```bash
   opentrack
   ```

2. **Select Tracker:**
   - Click the **Tracker** dropdown
   - Select **"neuralnet 1.1"** (requires ONNX Runtime)
   - Alternative: **"EasyTracker 1.1"** (if neuralnet doesn't work)

3. **Configure Tracker:**
   - Click the **hammer icon** next to Tracker
   - Select your webcam
   - Adjust exposure/brightness if needed
   - Click **OK**

4. **Configure Output:**
   - Click the **Output** dropdown
   - Select **"UDP over network"**
   - Click the **hammer icon** next to Output
   - Settings:
     - IP: `127.0.0.1`
     - Port: `5005`
   - Click **OK**

5. **Disable Game Protocols:**
   - Click **Options** → **Output**
   - Ensure no game protocols are enabled (we're using UDP only)

6. **Center Tracking:**
   - Sit in your natural position
   - Look straight at the screen
   - Press the **Center** button (or hotkey)
   - This sets your neutral head position

7. **Start Tracking:**
   - Click **Start**
   - You should see your face tracked in the camera preview
   - The 3D head visualization should move with your head

### Testing OpenTrack Output

Verify OpenTrack is sending UDP data:

```bash
# Listen to UDP port 5005
nc -lu 127.0.0.1 5005

# Or use this Python one-liner:
python3 -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(('127.0.0.1',5005)); print('Listening...'); print(s.recvfrom(48))"
```

You should see binary data arriving when you move your head.

---

## Testing & Calibration

### First Run

1. **Start OpenTrack** (as configured above)

2. **Start HeadMouse tracker:**
   ```bash
   opentrack-mouse-tracker
   ```

3. **First-time calibration:**

   The tracker will guide you through 5 steps:

   - **Step 1**: Look at the **CENTER** of your screen (neutral position)
   - **Step 2**: Look at the **TOP LEFT** corner
   - **Step 3**: Look at the **TOP RIGHT** corner
   - **Step 4**: Look at the **BOTTOM LEFT** corner
   - **Step 5**: Look at the **BOTTOM RIGHT** corner

   For each step:
   - Press ENTER when ready
   - Hold your gaze steady for 2 seconds
   - The tracker records your head position

   **Calibration is automatically saved to `~/.config/headmouse/calibration.json`**

4. **Start tracking:**
   - Press ENTER to begin
   - Move your head to control the mouse cursor
   - The cursor should follow your gaze

### Voice Control Commands

While the tracker is running, you can control it via command line (perfect for voice control integration):

```bash
# Toggle tracking on/off
opentrack-mouse toggle

# Recalibrate (live, without restarting)
opentrack-mouse calibrate
```

### i3wm Integration

For automatic window focus, add to `~/.config/i3/config`:

```
focus_follows_mouse yes
```

Reload i3: `i3-msg reload`

Now looking at a window will focus it!

---

## Troubleshooting

### OpenTrack Issues

**Problem: "library load failure" when selecting neuralnet tracker**

- ONNX Runtime not installed or not found
- Check: `ls /usr/local/lib/libonnxruntime.so*`
- Fix: Ensure `LD_LIBRARY_PATH` includes `/usr/local/lib`
  ```bash
  export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
  ```

**Problem: OpenTrack crashes on start**

- Missing dependencies
- Try: `ldd /usr/local/bin/opentrack` to see missing libs
- Install missing packages

**Problem: No camera detected**

- Check camera permissions: `ls -l /dev/video*`
- Add user to video group: `sudo usermod -a -G video $USER`
- Log out and back in

**Problem: Tracking is jittery/unstable**

- Improve lighting (face should be well-lit)
- Adjust camera settings in OpenTrack
- Reduce head movement speed during calibration
- Consider purchasing proper head tracking hardware

### HeadMouse Issues

**Problem: "No data from OpenTrack!" during calibration**

- OpenTrack not running or not started
- UDP output not configured (check port 5005)
- Firewall blocking localhost UDP (unlikely)

**Problem: Mouse movement too sensitive/insensitive**

- Recalibrate: `opentrack-mouse calibrate`
- During calibration, use more/less exaggerated head movements
- The calibration adapts to YOUR movement range

**Problem: Mouse movement inverted**

- This shouldn't happen with the calibrated version
- If it does, file a bug report

**Problem: Tracking drifts over time**

- Re-center OpenTrack at neutral position (press Center button)
- Recalibrate if drift persists

**Problem: Can't toggle/calibrate via commands**

- Check tracker is running: `ps aux | grep opentrack-mouse-tracker`
- Check PID file exists: `cat /tmp/opentrack_mouse.pid`
- Manually send signal: `kill -SIGUSR1 $(tail -1 /tmp/opentrack_mouse.pid)`

---

## Performance Tips

1. **Lighting**: Good, even lighting on your face improves tracking accuracy
2. **Camera position**: Camera should be at eye level, centered on your monitor
3. **Head position**: Sit comfortably, don't strain
4. **Calibration**: Recalibrate when lighting conditions change
5. **Hardware**: For serious use, consider dedicated head tracking hardware (TrackIR, Tobii, etc.)

---

## Upgrading HeadMouse

```bash
cd ~/HeadMouse
git pull
sudo cp opentrack-mouse-tracker.py /usr/local/bin/opentrack-mouse-tracker
sudo cp opentrack-mouse /usr/local/bin/opentrack-mouse
```

Your calibration in `~/.config/headmouse/` is preserved across upgrades.

---

## Uninstallation

### Remove HeadMouse:
```bash
sudo rm /usr/local/bin/opentrack-mouse-tracker
sudo rm /usr/local/bin/opentrack-mouse
rm -rf ~/.config/headmouse
```

### Remove OpenTrack:
```bash
cd /tmp/opentrack/build
sudo make uninstall
```

### Remove ONNX Runtime:
```bash
sudo rm /usr/local/lib/libonnxruntime*
sudo rm -rf /usr/local/include/onnxruntime
sudo ldconfig
```

---

## Additional Resources

- **OpenTrack Wiki**: https://github.com/opentrack/opentrack/wiki
- **ONNX Runtime Docs**: https://onnxruntime.ai/docs/
- **HeadMouse GitHub**: https://github.com/lawless-m/HeadMouse
- **i3wm User Guide**: https://i3wm.org/docs/userguide.html

---

## Credits

Built from scratch during a marathon session solving:
- ONNX Runtime compilation with Eigen hash mismatches
- OpenTrack NeuralNet tracker integration
- Multiple iterations of mouse control algorithms
- Calibration systems (fixed range → grid snapping → zone-based → calibrated direct)
- Voice control integration
- Persistent configuration

The final solution: calibrated direct mouse control with toggle and live recalibration support.

**License**: MIT
