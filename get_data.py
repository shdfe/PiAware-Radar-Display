import requests
import time
from threading import Thread, Lock
from config import FLIGHT_DATA_URL

URL = FLIGHT_DATA_URL

class FlightData:
    def __init__(self, update_interval=1.0):
        self.data = []
        self.lock = Lock()
        self.subscribers = []          
        self.update_interval = update_interval
        self.running = True
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while self.running:
            self.update_data()
            time.sleep(self.update_interval)

    def update_data(self):
        try:
            r = requests.get(URL, timeout=2)
            r.raise_for_status()
            with self.lock:
                self.data = r.json().get('aircraft', [])
                snapshot = list(self.data) 


            for callback in self.subscribers:
                callback(snapshot)
        except Exception as e:
            print(f"[FlightData ERROR] {e}")

    def subscribe(self, callback):
        """Add a callable that will be called with the latest snapshot"""
        self.subscribers.append(callback)

    def stop(self):
        self.running = False
        self.thread.join()

    def print_data(self):
        with self.lock:
            for aircraft in self.data:
                lat = aircraft.get('lat')
                lon = aircraft.get('lon')
                if lat is not None and lon is not None:
                    print(f"{aircraft.get('flight')} at LAT {lat} LON {lon}")
            print(f"Total: {len(self.data)}")

import math

class Calculations:
    @staticmethod
    def to_radar_coords(aircraft, radar_center=(37.4866, -122.16382)):
        """
        Convert lat/lon to radar coordinates (x, y) in meters
        Uses more accurate distance calculations for radar display
        """
        lat, lon = aircraft.get('lat'), aircraft.get('lon')
        if lat is None or lon is None:
            return None
        

        lat1_rad = math.radians(radar_center[0])
        lat2_rad = math.radians(lat)
        delta_lat = math.radians(lat - radar_center[0])
        delta_lon = math.radians(lon - radar_center[1])
        
        # Haversine formula for accurate distance calculation
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = 6371000 * c  
        
        # Calculate bearing
        y = math.sin(delta_lon) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
        bearing = math.atan2(y, x)
        

        radar_x = distance * math.sin(bearing)
        radar_y = -distance * math.cos(bearing)
        
        return (radar_x, radar_y)

    @staticmethod
    def process_aircraft(snapshot, radar_center=(37.4866, -122.16382)):
        """
        Convert snapshot list to list of tuples (callsign, x, y)
        """
        processed = []
        for ac in snapshot:
            coords = Calculations.to_radar_coords(ac, radar_center)
            if coords:
                callsign = ac.get('flight', 'UNKNOWN').strip()
                processed.append((callsign, *coords))
        return processed
