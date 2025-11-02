"""MAVLink log parser for extracting telemetry data from .bin files."""
from typing import Dict, List, Any, Optional
from pymavlink import mavutil
import numpy as np
import pandas as pd


class MAVLinkParser:
    """Parser for MAVLink binary log files."""
    
    def __init__(self, file_path: str):
        """Initialize parser with a .bin file path."""
        self.file_path = file_path
        self.mlog = None
        self.messages = {}
        self.metadata = {}
        self._parsed = False
        
    def parse(self) -> Dict[str, Any]:
        """Parse the MAVLink log file and extract all telemetry data."""
        if self._parsed:
            return self.get_summary()
            
        try:
            self.mlog = mavutil.mavlink_connection(self.file_path)
            self._extract_all_messages()
            self._compute_metadata()
            self._parsed = True
            return self.get_summary()
        except Exception as e:
            raise ValueError(f"Failed to parse MAVLink log: {str(e)}")
    
    def _extract_all_messages(self):
        """Extract all messages from the log file."""
        message_counts = {}
        
        while True:
            msg = self.mlog.recv_match(blocking=False)
            if msg is None:
                break
                
            msg_type = msg.get_type()
            
            # Skip invalid messages
            if msg_type in ['BAD_DATA']:
                continue
                
            # Initialize message type storage
            if msg_type not in self.messages:
                self.messages[msg_type] = []
                message_counts[msg_type] = 0
            
            # Store message data
            msg_dict = msg.to_dict()
            self.messages[msg_type].append(msg_dict)
            message_counts[msg_type] += 1
        
        self.metadata['message_counts'] = message_counts
        self.metadata['total_messages'] = sum(message_counts.values())
    
    def _compute_metadata(self):
        """Compute metadata and statistics from parsed messages."""
        # Extract time range
        if 'GPS' in self.messages and len(self.messages['GPS']) > 0:
            gps_times = [msg.get('TimeUS', 0) for msg in self.messages['GPS']]
            if gps_times:
                self.metadata['start_time_us'] = min(gps_times)
                self.metadata['end_time_us'] = max(gps_times)
                self.metadata['duration_seconds'] = (max(gps_times) - min(gps_times)) / 1e6
        
        # Extract altitude stats
        if 'GPS' in self.messages:
            altitudes = [msg.get('Alt', 0) for msg in self.messages['GPS'] if 'Alt' in msg]
            if altitudes:
                self.metadata['max_altitude_m'] = max(altitudes)
                self.metadata['min_altitude_m'] = min(altitudes)
                self.metadata['avg_altitude_m'] = np.mean(altitudes)
        
        # Extract battery stats
        if 'BAT' in self.messages or 'BATT' in self.messages:
            batt_key = 'BAT' if 'BAT' in self.messages else 'BATT'
            voltages = [msg.get('Volt', 0) for msg in self.messages[batt_key] if 'Volt' in msg]
            temps = [msg.get('Temp', 0) for msg in self.messages[batt_key] if 'Temp' in msg]
            
            if voltages:
                self.metadata['max_battery_voltage'] = max(voltages)
                self.metadata['min_battery_voltage'] = min(voltages)
            if temps:
                self.metadata['max_battery_temp'] = max(temps)
                self.metadata['min_battery_temp'] = min(temps)
        
        # Extract GPS status
        if 'GPS' in self.messages:
            gps_status = [msg.get('Status', 0) for msg in self.messages['GPS']]
            self.metadata['gps_fix_types'] = list(set(gps_status))
            
            # Find GPS signal loss events
            gps_loss_events = []
            for i, msg in enumerate(self.messages['GPS']):
                if msg.get('Status', 0) < 3:  # No 3D fix
                    gps_loss_events.append({
                        'index': i,
                        'time_us': msg.get('TimeUS', 0),
                        'status': msg.get('Status', 0)
                    })
            self.metadata['gps_loss_events'] = gps_loss_events
        
        # Extract error messages
        if 'ERR' in self.messages:
            errors = []
            for msg in self.messages['ERR']:
                errors.append({
                    'subsystem': msg.get('Subsys', 0),
                    'error_code': msg.get('ECode', 0),
                    'time_us': msg.get('TimeUS', 0)
                })
            self.metadata['errors'] = errors
        
        # Extract mode changes
        if 'MODE' in self.messages:
            mode_changes = []
            for msg in self.messages['MODE']:
                mode_changes.append({
                    'mode': msg.get('Mode', 0),
                    'mode_num': msg.get('ModeNum', 0),
                    'time_us': msg.get('TimeUS', 0)
                })
            self.metadata['mode_changes'] = mode_changes
        
        # Extract RC signal loss
        if 'RCIN' in self.messages:
            rc_loss_events = []
            for i, msg in enumerate(self.messages['RCIN']):
                # Check if all channels are zero or very low
                channels = [msg.get(f'C{j}', 0) for j in range(1, 9)]
                if all(c < 900 for c in channels):  # Typical RC loss threshold
                    rc_loss_events.append({
                        'index': i,
                        'time_us': msg.get('TimeUS', 0)
                    })
            self.metadata['rc_loss_events'] = rc_loss_events
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the parsed log data."""
        return {
            'parsed': self._parsed,
            'file_path': self.file_path,
            'metadata': self.metadata,
            'message_types': list(self.messages.keys()),
            'message_counts': self.metadata.get('message_counts', {})
        }
    
    def get_messages(self, msg_type: str, limit: Optional[int] = None) -> List[Dict]:
        """Get messages of a specific type."""
        if msg_type not in self.messages:
            return []
        
        messages = self.messages[msg_type]
        if limit:
            return messages[:limit]
        return messages
    
    def query_data(self, query: str) -> Dict[str, Any]:
        """
        Query the parsed data based on natural language query.
        This is a helper method for the LLM agent.
        """
        query_lower = query.lower()
        result = {}
        
        # Altitude queries
        if 'altitude' in query_lower or 'height' in query_lower:
            if 'max' in query_lower or 'highest' in query_lower:
                result['max_altitude_m'] = self.metadata.get('max_altitude_m')
            if 'min' in query_lower or 'lowest' in query_lower:
                result['min_altitude_m'] = self.metadata.get('min_altitude_m')
            if 'average' in query_lower or 'avg' in query_lower:
                result['avg_altitude_m'] = self.metadata.get('avg_altitude_m')
        
        # Battery queries
        if 'battery' in query_lower or 'voltage' in query_lower:
            result['battery_voltage_max'] = self.metadata.get('max_battery_voltage')
            result['battery_voltage_min'] = self.metadata.get('min_battery_voltage')
        
        if 'temperature' in query_lower and 'battery' in query_lower:
            result['battery_temp_max'] = self.metadata.get('max_battery_temp')
            result['battery_temp_min'] = self.metadata.get('min_battery_temp')
        
        # GPS queries
        if 'gps' in query_lower:
            result['gps_loss_events'] = self.metadata.get('gps_loss_events', [])
            result['gps_fix_types'] = self.metadata.get('gps_fix_types', [])
        
        # Flight time queries
        if 'flight time' in query_lower or 'duration' in query_lower:
            result['duration_seconds'] = self.metadata.get('duration_seconds')
            result['duration_minutes'] = self.metadata.get('duration_seconds', 0) / 60
        
        # Error queries
        if 'error' in query_lower:
            result['errors'] = self.metadata.get('errors', [])
        
        # RC signal queries
        if 'rc' in query_lower or 'radio' in query_lower or 'signal loss' in query_lower:
            result['rc_loss_events'] = self.metadata.get('rc_loss_events', [])
        
        return result
    
    def get_time_series(self, msg_type: str, field: str) -> Optional[pd.DataFrame]:
        """Get time series data for a specific message type and field."""
        if msg_type not in self.messages:
            return None
        
        data = []
        for msg in self.messages[msg_type]:
            if 'TimeUS' in msg and field in msg:
                data.append({
                    'time_us': msg['TimeUS'],
                    'value': msg[field]
                })
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        df['time_seconds'] = df['time_us'] / 1e6
        return df
    
    def detect_anomalies(self) -> Dict[str, List[Dict]]:
        """
        Detect potential anomalies in the flight data.
        Returns a dictionary of anomaly types and their occurrences.
        """
        anomalies = {
            'altitude_anomalies': [],
            'battery_anomalies': [],
            'gps_anomalies': [],
            'vibration_anomalies': [],
            'sudden_changes': []
        }
        
        # Altitude anomalies - sudden drops or climbs
        if 'GPS' in self.messages:
            altitudes = [(msg.get('TimeUS', 0), msg.get('Alt', 0)) 
                        for msg in self.messages['GPS'] if 'Alt' in msg]
            
            for i in range(1, len(altitudes)):
                time_diff = (altitudes[i][0] - altitudes[i-1][0]) / 1e6  # seconds
                alt_diff = altitudes[i][1] - altitudes[i-1][1]
                
                if time_diff > 0:
                    rate = alt_diff / time_diff
                    # Flag sudden altitude changes (>10 m/s)
                    if abs(rate) > 10:
                        anomalies['altitude_anomalies'].append({
                            'time_us': altitudes[i][0],
                            'rate_m_per_s': rate,
                            'altitude_change_m': alt_diff,
                            'severity': 'high' if abs(rate) > 20 else 'medium'
                        })
        
        # Battery anomalies - voltage drops
        batt_key = 'BAT' if 'BAT' in self.messages else 'BATT' if 'BATT' in self.messages else None
        if batt_key:
            voltages = [(msg.get('TimeUS', 0), msg.get('Volt', 0)) 
                       for msg in self.messages[batt_key] if 'Volt' in msg]
            
            for i in range(1, len(voltages)):
                volt_diff = voltages[i][1] - voltages[i-1][1]
                # Flag sudden voltage drops (>0.5V)
                if volt_diff < -0.5:
                    anomalies['battery_anomalies'].append({
                        'time_us': voltages[i][0],
                        'voltage_drop': volt_diff,
                        'severity': 'high' if volt_diff < -1.0 else 'medium'
                    })
        
        # GPS anomalies
        if self.metadata.get('gps_loss_events'):
            anomalies['gps_anomalies'] = self.metadata['gps_loss_events']
        
        # Vibration anomalies
        if 'VIBE' in self.messages:
            for msg in self.messages['VIBE']:
                vibe_x = msg.get('VibeX', 0)
                vibe_y = msg.get('VibeY', 0)
                vibe_z = msg.get('VibeZ', 0)
                
                # Flag high vibration levels (>30)
                if max(vibe_x, vibe_y, vibe_z) > 30:
                    anomalies['vibration_anomalies'].append({
                        'time_us': msg.get('TimeUS', 0),
                        'vibe_x': vibe_x,
                        'vibe_y': vibe_y,
                        'vibe_z': vibe_z,
                        'severity': 'high' if max(vibe_x, vibe_y, vibe_z) > 60 else 'medium'
                    })
        
        return anomalies
