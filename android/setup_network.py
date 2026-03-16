#!/usr/bin/env python3
"""
PyTrade Android Setup Helper
Auto-detects local IP and generates Android connection URLs
"""

import socket
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional, Tuple


def get_local_ip() -> Optional[str]:
    """Get local network IP address."""
    try:
        # Connect to a non-routable address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"❌ Error getting IP: {e}")
        return None


def get_windows_ip() -> Optional[str]:
    """Get Windows local IP using ipconfig."""
    try:
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            check=False
        )
        for line in result.stdout.split('\n'):
            if "IPv4" in line:
                # Format: "IPv4 Address . . . . . . . . . : 192.168.1.100"
                parts = line.split(":")
                if len(parts) > 1:
                    return parts[1].strip()
    except Exception as e:
        print(f"⚠️ Could not get Windows IP: {e}")
    return None


def check_port_open(host: str, port: int) -> bool:
    """Check if a port is reachable."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except Exception:
        return False


def generate_urls(host: str, port: int = 8501) -> Tuple[str, str]:
    """Generate direct and short URLs for Android."""
    direct_url = f"http://{host}:{port}"
    mobile_url = f"{direct_url}/?lang=th"
    return direct_url, mobile_url


def update_env_file(host: str, filepath: str = ".env.android") -> bool:
    """Update .env.android with detected IP."""
    try:
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace PYTRADE_HOST
        import re
        new_content = re.sub(
            r'PYTRADE_HOST=[\d\.]+',
            f'PYTRADE_HOST={host}',
            content
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        print(f"❌ Error updating .env.android: {e}")
        return False


def main():
    """Main setup helper."""
    print("=" * 60)
    print("🀖 PyTrade Android Setup Helper")
    print("=" * 60)
    print()
    
    # Get local IP
    print("πŸ" Finding your PC IP address...")
    local_ip = get_local_ip()
    if not local_ip:
        local_ip = get_windows_ip()
    
    if not local_ip:
        print("❌ Could not determine IP address")
        print("   Please manually check:")
        print("   - Windows: Settings > Network > ipconfig")
        print("   - macOS: System Preferences > Network")
        sys.exit(1)
    
    print(f"✅ Found IP: {local_ip}")
    print()
    
    # Check if Streamlit is running
    print("πŸ"Š Checking if Streamlit is running...")
    if check_port_open(local_ip, 8501):
        print("✅ Streamlit is running on port 8501")
    else:
        print("⚠️  Streamlit NOT running on port 8501")
        print("   Start it with: python -m streamlit run streamlit_app.py")
    print()
    
    # Generate URLs
    direct_url, mobile_url = generate_urls(local_ip)
    
    print("πŸ"— Android Connection URLs:")
    print("-" * 60)
    print(f"Direct URL:     {direct_url}")
    print(f"Mobile URL:     {mobile_url}")
    print()
    
    # QR Code generation (optional)
    try:
        import qrcode
        print("πŸ"ƒ Generating QR Code...")
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(mobile_url)
        qr.make(fit=True)
        print("QR Code ready (see QR_CODE.txt)")
        
        # Save QR as text
        with open("QR_CODE.txt", "w", encoding="utf-8") as f:
            f.write("PyTrade Android QR Code\n")
            f.write("=" * 40 + "\n")
            f.write(f"URL: {mobile_url}\n\n")
            img = qr.make_image()
            # Save as image
            img.save("pytrade_android_qr.png")
            print("✅ QR Code saved as pytrade_android_qr.png")
    except ImportError:
        print("πŸ" QRCode library not installed (optional)")
    print()
    
    # Update .env file
    print("πŸ" Updating .env.android...")
    if update_env_file(local_ip, ".env.android"):
        print("βœ… .env.android updated")
    else:
        print("⚠️  Could not update .env.android (manual update needed)")
    print()
    
    # Instructions
    print("πŸ" INSTRUCTIONS FOR ANDROID:")
    print("-" * 60)
    print()
    print("1. Open Chrome on your Android phone")
    print(f"2. Enter URL: {mobile_url}")
    print()
    print("3. To install as app:")
    print("   - Chrome Menu (β€") > 'Install app'")
    print("   - Or: Chrome Menu > 'Add to Home Screen'")
    print("   - App will appear on Android home screen")
    print()
    print("4. For internet access (without same WiFi):")
    print("   - On PC: ngrok http 8501")
    print("   - Copy ngrok URL")
    print("   - Edit .env.android: PYTRADE_HOST=<ngrok-url>")
    print()
    
    # Troubleshooting
    print("βš" TROUBLESHOOTING:")
    print("-" * 60)
    print()
    print("Cannot connect?")
    print("✓ Verify PC and Android on same WiFi")
    print(f"✓ Ping from PC: ping 127.0.0.1")
    print(f"✓ Check firewall allows port 8501")
    print(f"✓ Ensure Streamlit is running")
    print()
    
    # Copy to clipboard (Windows)
    if sys.platform == "win32":
        try:
            import pyperclip
            pyperclip.copy(mobile_url)
            print(f"βœ… URL copied to clipboard!")
        except ImportError:
            print(f"   (install pyperclip for clipboard copy)")
    
    print()
    print("=" * 60)
    print("✅ Setup complete! Ready for Android access.")
    print("=" * 60)


if __name__ == "__main__":
    main()
