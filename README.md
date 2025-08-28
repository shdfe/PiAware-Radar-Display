# WWII Radar Display - Live Flight Data

A real-time WWII-style radar display that shows live aircraft data from your PiAware ADS-B server. Features a rotating sweep line, range rings, and aircraft blips with authentic radar aesthetics. This application transforms live flight data into a vintage radar experience, complete with zoom, pan, and authentic blip effects.

## Features

- **Live Data**: Real-time aircraft position updates from your PiAware ADS-B server
- **WWII Aesthetics**: Classic green-on-black radar display with rotating sweep line
- **Range Rings**: Concentric circles showing distance from radar center
- **Aircraft Blips**: Red dots with white borders and flight call signs
- **Compass Rose**: North, East, South, West indicators around the display
- **Status Info**: Live aircraft count and timestamp display
- **Zoom & Pan**: Interactive zoom (0.5x to 4.0x) and mouse panning
- **Dual Modes**: Modern continuous display or authentic WWII blip mode

## How It Works

This application takes flight data from a PiAware ADS-B Server and creates a vintage radar display.

An ADS-B receiver receives transmissions from aircraft, containing the aircraft's GPS position, altitude, speed, and other data. FlightAware releases a PiAware kit which includes an ADS-B receiver and a Raspberry Pi computer which hosts a server that displays this data on a map.

My app takes that data and creates a vintage radar display. Broadly, this app takes the data from the server, transforms the coordinates from geographical coordinates to Cartesian coordinates that can be displayed on a screen. The radar display consists of a sweeping line which, when intersected with the coordinate of an aircraft, creates a blip which fades away over time, just like authentic WWII radar systems.

## Architecture

This project uses a **producer-consumer pattern** with real-time threading:

- **Producer**: `FlightData` class fetches data from your PiAware server every 0.3 seconds
- **Consumer**: `RadarDisplay` class processes the data and renders it on screen at 60 FPS
- **Threading**: Producer runs as a background daemon thread, consumer updates display in main thread
- **Coordinate Transformation**: Converts lat/lon to radar coordinates using Haversine formula for accuracy

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your radar**:
   - Edit `config.py` to set your radar center coordinates
   - Update `FLIGHT_DATA_URL` to point to your flight data server
   - Adjust display size and other preferences

3. **Run the radar**:
   ```bash
   python radar.py
   ```

## Configuration

Edit `config.py` to customize:

- **Radar Center**: Set your latitude/longitude coordinates
- **Flight Data URL**: Point to your aircraft.json endpoint
- **Display Size**: Change window dimensions
- **Range**: Adjust maximum radar range in kilometers
- **Colors**: Customize the radar color scheme

## Controls

- **ESC**: Exit the radar display
- **W**: Toggle between Modern and WWII radar modes
- **D**: Toggle debug mode (shows scaling grid and blip creation)
- **P**: Print current aircraft list to console
- **+/-**: Zoom in/out from center
- **Mouse Wheel**: Zoom in/out centered on mouse position
- **Left Click + Drag**: Pan around the radar view
- **R**: Reset zoom and pan to default
- **Real-time**: The display updates automatically every 0.3 seconds

## File Structure

- `radar.py` - Main radar display application with WWII mode, zoom/pan, and real-time rendering
- `get_data.py` - Flight data producer and coordinate calculations using Haversine formula
- `config.py` - Configuration settings for radar center, display, and performance

## Flight Data Format

Your PiAware server should provide JSON data in this format:
```json
{
  "aircraft": [
    {
      "flight": "UAL123",
      "lat": 37.7749,
      "lon": -122.4194,
    }
  ]
}
```

**Required Fields:**
- `flight`: Aircraft callsign/identifier
- `lat`: Latitude in decimal degrees
- `lon`: Longitude in decimal degrees

## Example Usage

```python
from radar import RadarDisplay

radar = RadarDisplay()
radar.run()
```
## WWII Mode
<img width="801" height="793" alt="image" src="https://github.com/user-attachments/assets/3bb7864c-1b43-41b2-be88-56c3c812e6ec" />

## Modern Mode
<img width="800" height="802" alt="image" src="https://github.com/user-attachments/assets/4f5ca2e6-1ea7-4d49-814a-c1042914efeb" />



## Technical Details

- **Coordinate System**: Uses Haversine formula for accurate distance calculations
- **Performance**: 60 FPS rendering with 0.3-second data updates
- **Memory Management**: Efficient blip lifecycle management with automatic cleanup
- **Thread Safety**: Producer-consumer pattern with proper locking for data access
