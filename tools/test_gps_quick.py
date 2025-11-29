#!/usr/bin/env python3
"""Quick GPS test - read data with longer timeout."""
import serial
import time

print("Testing GPS on /dev/serial0...")
print("Trying 9600 baud first...")

try:
    ser = serial.Serial('/dev/serial0', 9600, timeout=5)
    print("Connected. Waiting 10 seconds for GPS to send data...")
    time.sleep(10)
    
    data = ser.read(1000)
    print(f"\nReceived {len(data)} bytes")
    
    if data:
        text = data.decode('ascii', errors='ignore')
        lines = [l.strip() for l in text.split('\n') if l.strip()][:10]
        print("\nFirst 10 lines:")
        for i, line in enumerate(lines, 1):
            print(f"  {i}: {line[:80]}")
    else:
        print("No data received. Trying 115200 baud...")
        ser.close()
        
        ser = serial.Serial('/dev/serial0', 115200, timeout=5)
        print("Connected at 115200. Waiting 10 seconds...")
        time.sleep(10)
        
        data = ser.read(1000)
        print(f"\nReceived {len(data)} bytes at 115200 baud")
        
        if data:
            text = data.decode('ascii', errors='ignore')
            lines = [l.strip() for l in text.split('\n') if l.strip()][:10]
            print("\nFirst 10 lines:")
            for i, line in enumerate(lines, 1):
                print(f"  {i}: {line[:80]}")
        else:
            print("Still no data. GPS may need more time or antenna may not be connected.")
    
    ser.close()
except Exception as e:
    print(f"Error: {e}")

