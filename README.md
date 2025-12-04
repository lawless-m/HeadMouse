# HeadMouse - OpenTrack Mouse Control

Control your mouse cursor using head tracking via OpenTrack. Perfect for hands-free navigation in tiling window managers like i3wm.

## Features

- **Calibrated head tracking** - Maps your natural head movement range to screen coordinates
- **Persistent calibration** - Saves calibration between sessions (`~/.config/headmouse/`)
- **Live recalibration** - Recalibrate without restarting the tracker
- **Voice control ready** - Toggle and recalibrate via command line
- **Focus-follows-mouse integration** - Works seamlessly with i3wm's focus-follows-mouse

## Quick Start

**Already have OpenTrack installed?** Skip to [Usage](#usage).

**Fresh installation?** See **[INSTALLATION.md](INSTALLATION.md)** for complete setup guide including:
- Building ONNX Runtime from source
- Building OpenTrack with NeuralNet tracker support
- Fixing common build issues (Eigen hash mismatch, etc.)
- Complete OpenTrack configuration

## Requirements

- OpenTrack with UDP output enabled (port 5005)
- Python 3
- xdotool
- xdpyinfo

## Quick Installation (OpenTrack already installed)

```bash
# Install dependencies
sudo apt-get install xdotool x11-utils python3

# Install scripts
sudo cp opentrack-mouse-tracker.py /usr/local/bin/opentrack-mouse-tracker
sudo cp opentrack-mouse /usr/local/bin/opentrack-mouse
sudo chmod +x /usr/local/bin/opentrack-mouse-tracker
sudo chmod +x /usr/local/bin/opentrack-mouse
```

## OpenTrack Configuration

1. Open OpenTrack
2. Go to Output settings
3. Select "UDP over network"
4. Set port to 5005
5. Enable output
6. Center your tracking at neutral head position

## Usage

### First Run (Calibration)

```bash
opentrack-mouse-tracker
```

Follow the 5-step calibration:
1. Look at CENTER of screen
2. Look at TOP LEFT corner
3. Look at TOP RIGHT corner
4. Look at BOTTOM LEFT corner
5. Look at BOTTOM RIGHT corner

Press ENTER to start tracking. Calibration is automatically saved.

### Subsequent Runs

```bash
opentrack-mouse-tracker
```

Loads saved calibration automatically - no recalibration needed!

### Control Commands

```bash
# Toggle tracking on/off (useful for voice control)
opentrack-mouse toggle

# Delete calibration (will recalibrate on next start)
opentrack-mouse calibrate
```

## i3wm Integration

Add to your `~/.config/i3/config`:

```
focus_follows_mouse yes
```

Now you can look at a window to focus it!

## Voice Control Integration

If you're using voice control software, you can bind commands like:
- "toggle tracking" → `opentrack-mouse toggle`
- "recalibrate tracking" → `opentrack-mouse calibrate`

## How It Works

1. OpenTrack outputs 6-DOF tracking data via UDP (yaw, pitch, roll, x, y, z)
2. The tracker reads this data and uses yaw (left/right) and pitch (up/down)
3. Calibration measures your actual head movement range
4. Head position is mapped to screen coordinates
5. xdotool moves the mouse cursor to match your gaze
6. i3wm focuses the window under the cursor

## Troubleshooting

**No tracking data:**
- Make sure OpenTrack is running and outputting via UDP on port 5005
- Check that tracking is centered at your neutral position

**Mouse movement too sensitive/insensitive:**
- Delete calibration: `opentrack-mouse calibrate`
- Restart tracker and recalibrate with more exaggerated movements

**Tracking drift:**
- Recenter OpenTrack at your neutral position
- Recalibrate if needed

## Files

- `opentrack-mouse-tracker.py` - Main tracking script
- `opentrack-mouse` - Control script for toggle/calibrate commands
- `/tmp/opentrack_calibration.json` - Saved calibration data
- `/tmp/opentrack_mouse.pid` - PID file for control script

## License

MIT
