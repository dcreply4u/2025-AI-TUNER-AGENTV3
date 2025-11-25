# Theft Tracking Usage Examples

## Quick Start

### Option 2: WiFi Tracking (Default - Free)

```python
from services.theft_tracking_factory import create_wifi_tracking

# Create WiFi-based tracking (uses existing hardware, $0 cost)
tracking = create_wifi_tracking(
    vehicle_id="my_vehicle_001",
    update_interval=15.0,  # Update every 15 seconds
)

# Start tracking
tracking.start_tracking()

# Setup geofence
from services.theft_tracking_service import Geofence

home = Geofence(
    name="Home",
    center_lat=37.4219,
    center_lon=-122.0839,
    radius_meters=100.0,
    alert_on_exit=True,
)
tracking.add_geofence(home)

# Mark vehicle as parked
tracking.mark_parked(lat=37.4219, lon=-122.0839)

# Enable cloud upload (when WiFi available)
tracking.enable_cloud_upload("https://api.example.com/location")
```

### Option 1: Cellular Tracking (Premium - Always-On)

```python
from services.theft_tracking_factory import create_cellular_tracking

# Create cellular-based tracking ($30-70 hardware + $5-20/month)
tracking = create_cellular_tracking(
    vehicle_id="my_vehicle_001",
    cellular_port=None,  # Auto-detect
    update_interval=15.0,
)

# Start tracking
tracking.start_tracking()

# Setup geofence
from services.theft_tracking_service import Geofence

home = Geofence(
    name="Home",
    center_lat=37.4219,
    center_lon=-122.0839,
    radius_meters=100.0,
    alert_on_exit=True,
)
tracking.add_geofence(home)

# Enable cloud upload (always-on via cellular)
tracking.enable_cloud_upload("https://api.example.com/location")
```

## Upgrading/Downgrading

### Upgrade from WiFi to Cellular

```python
# Start with WiFi tracking
tracking = create_wifi_tracking(vehicle_id="vehicle_001")
tracking.start_tracking()

# Later, upgrade to cellular (when hardware is added)
success = tracking.upgrade_to_cellular()
if success:
    print("Upgraded to cellular tracking!")
else:
    print("Cellular modem not available - staying on WiFi")
```

### Downgrade from Cellular to WiFi

```python
# Currently using cellular
tracking = create_cellular_tracking(vehicle_id="vehicle_001")

# Downgrade to WiFi (to save on cellular costs)
tracking.downgrade_to_wifi()
print("Downgraded to WiFi tracking")
```

## Complete Example: Theft Tracking Setup

```python
from services.theft_tracking_factory import create_wifi_tracking
from services.theft_tracking_service import Geofence
from interfaces.gps_interface import GPSInterface

# Initialize GPS
gps = GPSInterface(port="/dev/ttyUSB1")

# Create tracking service (Option 2: WiFi - Free)
tracking = create_wifi_tracking(
    vehicle_id="race_car_001",
    gps_interface=gps,
    update_interval=15.0,
)

# Setup alert callback
def handle_theft_alert(alert):
    print(f"🚨 THEFT ALERT: {alert.alert_type}")
    print(f"   Location: {alert.location}")
    print(f"   Message: {alert.message}")
    print(f"   Severity: {alert.severity}")
    
    # Send push notification
    # send_push_notification(alert.message)
    
    # Send email
    # send_email("theft@example.com", "Theft Alert", alert.message)
    
    # Call law enforcement API (if configured)
    # notify_law_enforcement(alert)

tracking.register_alert_callback(handle_theft_alert)

# Add home geofence
home_geofence = Geofence(
    name="Home Garage",
    center_lat=37.4219,
    center_lon=-122.0839,
    radius_meters=50.0,  # 50 meter radius
    alert_on_exit=True,
    alert_on_enter=False,
)
tracking.add_geofence(home_geofence)

# Add track geofence
track_geofence = Geofence(
    name="Race Track",
    center_lat=37.5000,
    center_lon=-122.2000,
    radius_meters=500.0,  # 500 meter radius
    alert_on_exit=False,
    alert_on_enter=True,  # Alert when entering track
)
tracking.add_geofence(track_geofence)

# Enable cloud upload
tracking.enable_cloud_upload("https://api.telemetryiq.com/location")

# Start tracking
tracking.start_tracking()

# Mark vehicle as parked when done
tracking.mark_parked(lat=37.4219, lon=-122.0839)

# Later, check location
location = tracking.get_current_location()
if location:
    print(f"Current location: {location.latitude}, {location.longitude}")
    print(f"Speed: {location.speed_mps * 2.237:.1f} mph")
    print(f"Connection: {location.connection_type}")

# Check for alerts
alerts = tracking.get_recent_alerts(limit=5)
for alert in alerts:
    if not alert.acknowledged:
        print(f"Unacknowledged alert: {alert.message}")
```

## Mobile App Integration

### Get Current Location

```javascript
// JavaScript/React Native
async function getVehicleLocation(vehicleId) {
  const response = await fetch(
    `https://api.example.com/api/theft-tracking/vehicles/${vehicleId}/location`
  );
  const location = await response.json();
  
  return {
    lat: location.latitude,
    lng: location.longitude,
    speed: location.speed_mps * 2.237, // Convert to mph
    heading: location.heading,
    timestamp: location.timestamp,
    connection: location.connection_type,
  };
}

// Display on map
function updateMap(location) {
  map.setCenter({ lat: location.lat, lng: location.lng });
  marker.setPosition({ lat: location.lat, lng: location.lng });
}
```

### Upgrade to Cellular

```javascript
async function upgradeToCellular(vehicleId) {
  const response = await fetch(
    `https://api.example.com/api/theft-tracking/vehicles/${vehicleId}/upgrade/cellular`,
    { method: 'POST' }
  );
  const result = await response.json();
  
  if (result.status === 'upgraded') {
    showNotification('Upgraded to cellular tracking!');
  } else {
    showError('Failed to upgrade - cellular modem not found');
  }
}
```

### Get Connection Status

```javascript
async function getConnectionStatus(vehicleId) {
  const response = await fetch(
    `https://api.example.com/api/theft-tracking/vehicles/${vehicleId}/connection/status`
  );
  const status = await response.json();
  
  return {
    type: status.connection_type, // "wifi", "cellular", "local"
    status: status.status, // "connected", "disconnected"
    signal: status.signal_strength,
    cellularAvailable: status.cellular_available,
    wifiAvailable: status.wifi_available,
  };
}
```

## Fleet Management Integration

```python
from services.fleet_management import FleetManagement
from services.fleet_theft_tracking import FleetTheftTracking
from services.theft_tracking_factory import create_wifi_tracking

# Initialize fleet
fleet = FleetManagement()
fleet_tracking = FleetTheftTracking(fleet)

# Register vehicles with WiFi tracking (Option 2)
for vehicle_id in ["vehicle_001", "vehicle_002", "vehicle_003"]:
    tracking = create_wifi_tracking(vehicle_id=vehicle_id)
    fleet_tracking.register_vehicle(vehicle_id, tracking)
    tracking.start_tracking()

# Upgrade one vehicle to cellular (Option 1)
premium_vehicle = fleet_tracking.tracking_services["vehicle_001"]
premium_vehicle.upgrade_to_cellular()

# Get all vehicle locations
locations = fleet_tracking.get_all_locations()
for vehicle_id, location in locations.items():
    if location:
        print(f"{vehicle_id}: {location['latitude']}, {location['longitude']}")

# Get vehicles with alerts
vehicles_in_alert = fleet_tracking.get_vehicles_in_alert()
if vehicles_in_alert:
    print(f"Vehicles with alerts: {vehicles_in_alert}")
```

## Connection Status Monitoring

```python
# Check connection status
conn_status = tracking.get_connection_status()
if conn_status:
    print(f"Connection Type: {conn_status.connection_type}")
    print(f"Status: {conn_status.status}")
    print(f"Signal Strength: {conn_status.signal_strength}")
    
    if conn_status.connection_type == "cellular":
        print("✅ Using cellular tracking (Option 1)")
    elif conn_status.connection_type == "wifi":
        print("✅ Using WiFi tracking (Option 2)")
    else:
        print("⚠️ Using local storage only")

# Check if cellular is available (for upgrade)
if tracking.is_cellular_available():
    print("Cellular modem detected - can upgrade to Option 1")
else:
    print("Cellular modem not available - using Option 2 (WiFi)")
```

## Alert Handling

```python
# Register multiple alert handlers
def email_alert(alert):
    if alert.severity in ["high", "critical"]:
        send_email("owner@example.com", "Theft Alert", alert.message)

def sms_alert(alert):
    if alert.severity == "critical":
        send_sms("+1234567890", f"THEFT ALERT: {alert.message}")

def push_notification(alert):
    send_push_notification(
        title="Theft Alert",
        body=alert.message,
        data={"location": alert.location}
    )

tracking.register_alert_callback(email_alert)
tracking.register_alert_callback(sms_alert)
tracking.register_alert_callback(push_notification)
```

## Best Practices

### 1. Start with WiFi (Option 2)
```python
# Default: Free WiFi tracking
tracking = create_wifi_tracking(vehicle_id="vehicle_001")
```

### 2. Upgrade When Needed
```python
# Upgrade to cellular for high-value vehicles
if vehicle_value > 50000:
    tracking.upgrade_to_cellular()
```

### 3. Monitor Connection Status
```python
# Regularly check connection
conn = tracking.get_connection_status()
if conn.status == "disconnected":
    # Handle disconnection
    pass
```

### 4. Setup Geofences
```python
# Add multiple geofences
tracking.add_geofence(home_geofence)
tracking.add_geofence(work_geofence)
tracking.add_geofence(garage_geofence)
```

### 5. Enable Cloud Upload
```python
# Always enable cloud upload for backup
tracking.enable_cloud_upload("https://api.example.com/location")
```

## Troubleshooting

### WiFi Not Connecting
```python
# Check WiFi status
if not tracking.is_wifi_available():
    print("WiFi not available - using local storage")
    # Location will be stored locally and uploaded when WiFi available
```

### Cellular Modem Not Detected
```python
# Check if cellular is available
if not tracking.is_cellular_available():
    print("Cellular modem not detected")
    # Check hardware connections
    # Verify SIM card is inserted
    # Check modem power
```

### No GPS Signal
```python
# Check GPS availability
if not tracking.gps_available:
    print("GPS not available")
    # Check GPS module connection
    # Verify GPS antenna
```

## Summary

- **Option 2 (WiFi)**: Default, free, uses existing hardware
- **Option 1 (Cellular)**: Premium, always-on, requires hardware + monthly fee
- **Easy Upgrade**: Can upgrade/downgrade at any time
- **Automatic Failover**: System automatically switches between WiFi and Cellular
- **Local Storage**: Always stores location locally, even when offline






