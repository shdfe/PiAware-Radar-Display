import pygame
import math
import time
from threading import Thread, Lock
from get_data import FlightData, Calculations
from config import *

class RadarDisplay:
    def __init__(self, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT):
        pygame.init()
        self.width = width
        self.height = height
        self.center = (width // 2, height // 2)
        self.radius = min(width, height) // 2 - 50
        
        self.screen = pygame.display.set_mode([width, height])
        pygame.display.set_caption("WWII Radar Display - Live Flight Data")
        self.clock = pygame.time.Clock()
        
        self.sweep_angle = 0
        self.last_sweep_angle = 0
        self.sweep_speed = SWEEP_SPEED
        self.sweep_cycle = 0 
        self.last_blip_cycle_by_callsign = {}
        self.aircraft_data = []
        self.data_lock = Lock()
        self.debug_mode = False
        
        self.wwii_mode = False
        self.blips = []
        self.lead_degrees = 5 
        
        self.zoom_level = 1.0
        self.min_zoom = 0.5 
        self.max_zoom = 4.0 
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.last_mouse_pos = None
        
        self.BLACK = COLORS['BLACK']
        self.GREEN = COLORS['GREEN']
        self.DARK_GREEN = COLORS['DARK_GREEN']
        self.WHITE = COLORS['WHITE']
        self.YELLOW = COLORS['YELLOW']
        self.RED = COLORS['RED']
        
        self.flight_data = FlightData(update_interval=FLIGHT_DATA_UPDATE_INTERVAL)
        self.flight_data.subscribe(self.update_aircraft_data)
        
        self.radar_center = RADAR_CENTER
        
    def update_aircraft_data(self, snapshot):
        with self.data_lock:
            self.aircraft_data = Calculations.process_aircraft(snapshot, self.radar_center)
            
        self.print_aircraft_list(snapshot)
    
    def print_aircraft_list(self, snapshot):
        print(f"\n=== Aircraft Update at {time.strftime('%H:%M:%S')} ===")
        if snapshot:
            for aircraft in snapshot:
                flight = aircraft.get('flight', 'UNKNOWN').strip()
                lat = aircraft.get('lat')
                lon = aircraft.get('lon')
                alt = aircraft.get('alt', 'N/A')
                speed = aircraft.get('speed', 'N/A')
                
                if lat is not None and lon is not None:
                    radar_coords = Calculations.to_radar_coords(aircraft, self.radar_center)
                    if radar_coords:
                        radar_x, radar_y = radar_coords
                        distance_km = math.sqrt(radar_x**2 + radar_y**2) / 1000
                        
                        scale_factor = self.radius / (MAX_RANGE_KM * 1000)
                        scaled_x = radar_x * scale_factor
                        scaled_y = radar_y * scale_factor
                        
                        print(f"✈️  {flight}: Lat {lat:.4f}, Lon {lon:.4f} | Raw Radar X={radar_x:.1f}m, Y={radar_y:.1f}m | Scaled X={scaled_x:.1f}, Y={scaled_y:.1f} | Distance: {distance_km:.1f}km | Alt {alt}, Speed {speed}")
                    else:
                        print(f"✈️  {flight}: Lat {lat:.4f}, Lon {lon:.4f} | Radar: Out of range | Alt {alt}, Speed {speed}")
                else:
                    print(f"✈️  {flight}: Position unavailable")
            print(f"Total aircraft: {len(snapshot)}")
        else:
            print("No aircraft detected")
        print("=" * 50)
    
    def draw_range_rings(self):
        for i in range(1, RANGE_RINGS + 1):
            radius = (self.radius * i) // RANGE_RINGS
            
            transformed_center = self.apply_transform(self.center)
            transformed_radius = int(radius * self.zoom_level)
            
            pygame.draw.circle(self.screen, self.DARK_GREEN, transformed_center, transformed_radius, 1)
            
            range_km = (i * MAX_RANGE_KM) // RANGE_RINGS
            font = pygame.font.Font(None, 24)
            text = font.render(f"{range_km}km", True, self.DARK_GREEN)
            text_pos = (transformed_center[0] + transformed_radius - 20, transformed_center[1] - 10)
            self.screen.blit(text, text_pos)
    
    def draw_sweep_line(self):
        end_x = self.center[0] + self.radius * math.cos(math.radians(self.sweep_angle))
        end_y = self.center[1] - self.radius * math.sin(math.radians(self.sweep_angle))
        
        transformed_center = self.apply_transform(self.center)
        transformed_end = self.apply_transform((end_x, end_y))
        
        pygame.draw.line(self.screen, self.GREEN, transformed_center, transformed_end, 2)
        
        for i in range(1, 10):
            fade_alpha = 255 - (i * 25)
            if fade_alpha > 0:
                fade_radius = self.radius - (i * 20)
                if fade_radius > 0:
                    fade_x = self.center[0] + fade_radius * math.cos(math.radians(self.sweep_angle))
                    fade_y = self.center[1] - fade_radius * math.sin(math.radians(self.sweep_angle))
                    fade_color = (0, fade_alpha, 0)
                    fade_start = self.apply_transform(self.center)
                    fade_end = self.apply_transform((fade_x, fade_y))
                    pygame.draw.line(self.screen, fade_color, fade_start, fade_end, 1)
    
    def draw_aircraft(self):
        with self.data_lock:
            if self.wwii_mode:
                self.draw_wwii_blips()
            else:
                self.draw_modern_aircraft()
    
    def draw_modern_aircraft(self):
        for callsign, x, y in self.aircraft_data:
            scale_factor = self.radius / (MAX_RANGE_KM * 1000) 
            scaled_x = x * scale_factor
            scaled_y = y * scale_factor
            
            screen_x = self.center[0] + int(scaled_x)
            screen_y = self.center[1] + int(scaled_y)
            
            distance = math.sqrt(x**2 + y**2)
            if distance <= MAX_RANGE_KM * 1000: 
                transformed_pos = self.apply_transform((screen_x, screen_y))
                
                pygame.draw.circle(self.screen, self.RED, transformed_pos, 4)
                pygame.draw.circle(self.screen, self.WHITE, transformed_pos, 4, 1)
                
                font = pygame.font.Font(None, 20)
                text = font.render(callsign, True, self.WHITE)
                text_pos = (transformed_pos[0] + 10, transformed_pos[1] - 10)
                self.screen.blit(text, text_pos)
                if self.debug_mode:
                    transformed_center = self.apply_transform(self.center)
                    pygame.draw.line(self.screen, self.YELLOW, transformed_center, transformed_pos, 1)
    
    def update_wwii_blips(self):
        new_blips = []
        
        for callsign, x, y in self.aircraft_data:
            scale_factor = self.radius / (MAX_RANGE_KM * 1000)
            scaled_x = x * scale_factor
            scaled_y = y * scale_factor
            
            screen_x = self.center[0] + int(scaled_x)
            screen_y = self.center[1] + int(scaled_y)
            
            dx = screen_x - self.center[0]
            dy = screen_y - self.center[1]
            position_angle = math.degrees(math.atan2(dx, -dy)) % 360
            trigger_angle = (position_angle - self.lead_degrees) % 360

            already_blipped = self.last_blip_cycle_by_callsign.get(callsign) == self.sweep_cycle
            if not already_blipped:
                new_blips.append((screen_x, screen_y, 0, 255, callsign))
                self.last_blip_cycle_by_callsign[callsign] = self.sweep_cycle
                if self.debug_mode:
                    print(f"🎯 Blip created for {callsign} at sweep angle {self.sweep_angle:.1f}°")
        
        updated_blips = []
        for x, y, age, intensity, callsign in self.blips:
            new_age = age + 1
            new_intensity = max(0, intensity - 12) 
            
            if new_intensity > 0:
                updated_blips.append((x, y, new_age, new_intensity, callsign))
        
        self.blips = new_blips + updated_blips
    
    def draw_wwii_blips(self):
        for x, y, age, intensity, callsign in self.blips:
            if intensity > 0:
                transformed_pos = self.apply_transform((x, y))
                
                if age == 0:
                    pygame.draw.circle(self.screen, (0, intensity, 0), transformed_pos, 4)
                    pygame.draw.circle(self.screen, (0, intensity//2, 0), transformed_pos, 8)
                    pygame.draw.circle(self.screen, (0, intensity//4, 0), transformed_pos, 12)
                else: 
                    pygame.draw.circle(self.screen, (0, intensity, 0), transformed_pos, 2)
                    pygame.draw.circle(self.screen, (0, intensity//2, 0), transformed_pos, 4)
                
                if age <= 2:
                    font = pygame.font.Font(None, 20)
                    text = font.render(callsign, True, (0, intensity, 0))
                    text_pos = (transformed_pos[0] + 10, transformed_pos[1] - 10)
                    self.screen.blit(text, text_pos)
    
    def draw_compass_rose(self):
        directions = ['N', 'E', 'S', 'W']
        for i, direction in enumerate(directions):
            angle = i * 90
            x = self.center[0] + (self.radius + 30) * math.cos(math.radians(angle))
            y = self.center[1] - (self.radius + 30) * math.sin(math.radians(angle))
            
            transformed_pos = self.apply_transform((x, y))
            
            font = pygame.font.Font(None, 28)
            text = font.render(direction, True, self.WHITE)
            text_rect = text.get_rect(center=transformed_pos)
            self.screen.blit(text, text_rect)
    
    def draw_debug_grid(self):
        """Draw debug grid to show scaling"""
        if not self.debug_mode:
            return
            
        for i in range(1, 6):
            grid_radius = (self.radius * i) // 5
            pygame.draw.circle(self.screen, self.YELLOW, self.center, grid_radius, 1)
            
            grid_km = (i * MAX_RANGE_KM) // 5
            font = pygame.font.Font(None, 18)
            text = font.render(f"{grid_km}km", True, self.YELLOW)
            text_pos = (self.center[0] + grid_radius - 15, self.center[1] - 8)
            self.screen.blit(text, text_pos)
    
    def zoom_in(self):
        self.zoom_level = min(self.max_zoom, self.zoom_level * 1.2)
        print(f"Zoom: {self.zoom_level:.1f}x")
    
    def zoom_out(self):
        self.zoom_level = max(self.min_zoom, self.zoom_level / 1.2)
        print(f"Zoom: {self.zoom_level:.1f}x")
    
    def zoom_in_at_point(self, point):
        old_zoom = self.zoom_level
        self.zoom_level = min(self.max_zoom, self.zoom_level * 1.2)
        
        zoom_factor = self.zoom_level / old_zoom
        self.pan_x = point[0] - (point[0] - self.pan_x) * zoom_factor
        self.pan_y = point[1] - (point[1] - self.pan_y) * zoom_factor
        print(f"Zoom: {self.zoom_level:.1f}x at point")
    
    def zoom_out_at_point(self, point):
        old_zoom = self.zoom_level
        self.zoom_level = max(self.min_zoom, self.zoom_level / 1.2)
        
        zoom_factor = self.zoom_level / old_zoom
        self.pan_x = point[0] - (point[0] - self.pan_x) * zoom_factor
        self.pan_y = point[1] - (point[1] - self.pan_y) * zoom_factor
        print(f"Zoom: {self.zoom_level:.1f}x at point")
    
    def reset_view(self):
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
    
    def is_sweep_intersecting(self, x, y, sweep_range=5):
       
        dx = x - self.center[0]
        dy = y - self.center[1]
        position_angle = math.degrees(math.atan2(dx, -dy)) % 360
        

        angle_diff = abs((position_angle - self.sweep_angle + 180) % 360 - 180)
        
        return angle_diff <= sweep_range

    def did_sweep_cross_angle(self, target_angle):
        
        a0 = self.last_sweep_angle % 360
        a1 = self.sweep_angle % 360
        t  = target_angle % 360
        if a0 <= a1:
            return a0 <= t <= a1
        
        return t >= a0 or t <= a1
    
    def apply_transform(self, point):
        
        x, y = point
        
        zoomed_x = (x - self.center[0]) * self.zoom_level + self.center[0]
        zoomed_y = (y - self.center[1]) * self.zoom_level + self.center[1]
        
        return (int(zoomed_x + self.pan_x), int(zoomed_y + self.pan_y))
    
    def draw_status_info(self):
        
        with self.data_lock:
            aircraft_count = len(self.aircraft_data)
        
        font = pygame.font.Font(None, 24)
        status_text = f"Aircraft: {aircraft_count} | Sweep: {self.sweep_angle:.1f}°"
        text = font.render(status_text, True, self.WHITE)
        self.screen.blit(text, (10, 10))
        
        
        timestamp = time.strftime("%H:%M:%S")
        time_text = font.render(timestamp, True, self.WHITE)
        self.screen.blit(time_text, (10, 35))
        
        
        controls_text = "ESC: Exit | P: Print Aircraft List | D: Debug Mode | W: WWII Mode"
        controls_surface = font.render(controls_text, True, self.WHITE)
        self.screen.blit(controls_surface, (10, 60))
        
        
        zoom_text = f"Zoom: {self.zoom_level:.1f}x | Pan: ({self.pan_x}, {self.pan_y})"
        zoom_surface = font.render(zoom_text, True, self.WHITE)
        self.screen.blit(zoom_surface, (10, 85))
        
        
        mode_text = f"Mode: {'WWII Radar' if self.wwii_mode else 'Modern'}"
        mode_color = self.GREEN if self.wwii_mode else self.WHITE
        mode_surface = font.render(mode_text, True, mode_color)
        self.screen.blit(mode_surface, (10, 135))
        
        
        zoom_controls = "+/-: Zoom | Mouse: Pan | R: Reset | Wheel: Zoom at Point"
        zoom_controls_surface = font.render(zoom_controls, True, self.WHITE)
        self.screen.blit(zoom_controls_surface, (10, 110))
    
    def run(self):
        
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_p:  
                        with self.data_lock:
                            if self.aircraft_data:
                                print(f"\n=== Current Aircraft on Radar Display at {time.strftime('%H:%M:%S')} ===")
                                for callsign, x, y in self.aircraft_data:
                                    distance_km = math.sqrt(x**2 + y**2) / 1000
                                    bearing = math.degrees(math.atan2(x, y)) % 1000
                                    print(f"📍 {callsign}: Radar X={x:.1f}m, Y={y:.1f}m | Distance: {distance_km:.1f}km | Bearing: {bearing:.1f}°")
                                print(f"Total on radar: {len(self.aircraft_data)}")
                            else:
                                print("No aircraft currently on radar display")
                            print("=" * 50)
                    elif event.key == pygame.K_d:  
                        self.debug_mode = not self.debug_mode
                        print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
                    elif event.key == pygame.K_w:  
                        self.wwii_mode = not self.wwii_mode
                        if self.wwii_mode:
                            self.blips = []  
                        print(f"WWII Radar Mode: {'ON' if self.wwii_mode else 'OFF'}")
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:  
                        self.zoom_in()
                    elif event.key == pygame.K_MINUS:  
                        self.zoom_out()
                    elif event.key == pygame.K_r:  
                        self.reset_view()
                        print("View reset to default")
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  
                        self.is_panning = True
                        self.last_mouse_pos = event.pos
                    elif event.button == 4:  
                        self.zoom_in_at_point(event.pos)
                    elif event.button == 5:  
                        self.zoom_out_at_point(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  
                        self.is_panning = False
                elif event.type == pygame.MOUSEMOTION:
                    if self.is_panning and self.last_mouse_pos:
                        dx = event.pos[0] - self.last_mouse_pos[0]
                        dy = event.pos[1] - self.last_mouse_pos[1]
                        self.pan_x += dx
                        self.pan_y += dy
                        self.last_mouse_pos = event.pos
            
            prev = self.sweep_angle
            self.last_sweep_angle = prev
            self.sweep_angle = (prev + self.sweep_speed) % 360
            if prev > self.sweep_angle:  
                self.sweep_cycle += 1
            if self.wwii_mode:
                self.update_wwii_blips()

            self.screen.fill(self.BLACK)

            self.draw_range_rings()
            self.draw_compass_rose()
            if self.debug_mode:
                self.draw_debug_grid()
            self.draw_aircraft()
            self.draw_sweep_line()
            self.draw_status_info()

            pygame.display.flip()
            self.clock.tick(FPS)
        
        self.flight_data.stop()
        pygame.quit()

if __name__ == "__main__":
    radar = RadarDisplay()
    radar.run()

