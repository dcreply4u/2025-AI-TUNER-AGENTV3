"""
Check Video Metadata for Embedded Telemetry

This script inspects MP4 video files to check for embedded telemetry data
or metadata that might contain telemetry information.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_video_metadata(video_path: Path) -> dict:
    """Check video file for metadata and embedded telemetry."""
    result = {
        "file": str(video_path),
        "exists": video_path.exists(),
        "size_mb": 0.0,
        "video_info": {},
        "metadata": {},
        "has_telemetry": False,
        "telemetry_format": None
    }
    
    if not video_path.exists():
        return result
    
    result["size_mb"] = video_path.stat().st_size / (1024 * 1024)
    
    # Try OpenCV
    try:
        import cv2
        cap = cv2.VideoCapture(str(video_path))
        if cap.isOpened():
            result["video_info"] = {
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "duration_sec": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0,
            }
            cap.release()
    except ImportError:
        result["video_info"]["error"] = "OpenCV not available"
    except Exception as e:
        result["video_info"]["error"] = str(e)
    
    # Try ffprobe (if available) for detailed metadata
    try:
        import subprocess
        import json
        
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if output.returncode == 0:
            probe_data = json.loads(output.stdout)
            result["metadata"] = probe_data.get("format", {})
            
            # Check for telemetry-related metadata
            format_tags = probe_data.get("format", {}).get("tags", {})
            if format_tags:
                # Look for telemetry-related tags
                telemetry_keywords = ["telemetry", "data", "sensor", "rpm", "speed", "gps", "can"]
                for key, value in format_tags.items():
                    key_lower = key.lower()
                    if any(kw in key_lower for kw in telemetry_keywords):
                        result["has_telemetry"] = True
                        result["telemetry_format"] = f"Metadata tag: {key}"
                        result["metadata"]["telemetry_tags"] = {key: value}
        else:
            result["metadata"]["ffprobe_error"] = "ffprobe not available or failed"
    except FileNotFoundError:
        result["metadata"]["ffprobe_error"] = "ffprobe not found (install FFmpeg)"
    except Exception as e:
        result["metadata"]["ffprobe_error"] = str(e)
    
    # Check file for embedded data streams
    try:
        with open(video_path, 'rb') as f:
            # Read first 1KB to check for file signatures
            header = f.read(1024)
            
            # Check for MP4 box structure
            if b'ftyp' in header or b'moov' in header or b'mdat' in header:
                result["metadata"]["container"] = "MP4"
            
            # Look for telemetry-related strings in header
            telemetry_strings = [b"telemetry", b"RPM", b"SPEED", b"GPS", b"CAN", b"OBD"]
            found_strings = []
            for ts in telemetry_strings:
                if ts in header:
                    found_strings.append(ts.decode('utf-8', errors='ignore'))
            
            if found_strings:
                result["has_telemetry"] = True
                result["telemetry_format"] = f"Embedded strings: {', '.join(found_strings)}"
                result["metadata"]["found_strings"] = found_strings
    except Exception as e:
        result["metadata"]["read_error"] = str(e)
    
    return result


def main():
    """Check videos on USB drive."""
    usb_path = Path("E:/DCIM/100ADVID")
    
    if not usb_path.exists():
        print(f"USB path not found: {usb_path}")
        return
    
    video_files = list(usb_path.glob("*.mp4"))
    
    if not video_files:
        print("No MP4 files found")
        return
    
    print(f"Found {len(video_files)} video files")
    print("=" * 80)
    
    # Check first few videos
    for video_file in sorted(video_files)[:5]:  # Check first 5
        print(f"\n📹 Checking: {video_file.name}")
        result = check_video_metadata(video_file)
        
        print(f"  Size: {result['size_mb']:.2f} MB")
        
        if result["video_info"]:
            vi = result["video_info"]
            if "error" not in vi:
                print(f"  Resolution: {vi.get('width', 0)}x{vi.get('height', 0)}")
                print(f"  FPS: {vi.get('fps', 0):.2f}")
                print(f"  Duration: {vi.get('duration_sec', 0):.2f} seconds")
        
        if result["has_telemetry"]:
            print(f"  ✅ TELEMETRY DETECTED: {result['telemetry_format']}")
        else:
            print(f"  ❌ No telemetry detected")
        
        if result["metadata"].get("telemetry_tags"):
            print(f"  Metadata tags: {result['metadata']['telemetry_tags']}")
    
    print("\n" + "=" * 80)
    print("Summary: Checked video files for embedded telemetry")
    print("If telemetry is found, it may need special extraction code")


if __name__ == "__main__":
    main()

