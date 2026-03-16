#!/usr/bin/env python3
"""
PyTrade MT5 Connection Tester & Setup Helper
ทดสอบเชื่อมต่อ MT5 และหาค่าการตั้งค่าที่ต้องการ
"""

import os
import sys
import subprocess
from pathlib import Path
import socket
from typing import Optional, Tuple


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_ok(msg: str):
    """Print success message."""
    print(f"✅ {msg}")


def print_warn(msg: str):
    """Print warning message."""
    print(f"⚠️  {msg}")


def print_error(msg: str):
    """Print error message."""
    print(f"❌ {msg}")


def find_mt5_executable() -> Optional[str]:
    """Find MT5 terminal64.exe on Windows."""
    print_header("Step 1: Finding MT5 Terminal")
    
    # Common paths
    common_paths = [
        r"C:\Program Files\MetaTrader 5\terminal64.exe",
        r"C:\Program Files\MetaTrader 5\terminal.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal.exe",
    ]
    
    print("Searching common locations...")
    for path_str in common_paths:
        path = Path(path_str)
        if path.exists():
            print_ok(f"Found: {path}")
            return str(path)
    
    print_warn("Not found in common locations, searching disk...")
    
    # Search in common drives
    try:
        result = subprocess.run(
            ["powershell", "-Command", 
             "Get-ChildItem -Path 'C:\\' -Filter 'terminal*.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 FullName"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.stdout.strip():
            path = result.stdout.strip()
            print_ok(f"Found: {path}")
            return path
    except Exception as e:
        print_error(f"Search failed: {e}")
    
    print_error("MT5 Terminal not found!")
    print("Please install MetaTrader 5 from: https://www.metaquotes.net/en/metatrader5")
    return None


def get_mt5_account_info() -> Optional[Tuple[str, str, str]]:
    """Get MT5 account info from user input."""
    print_header("Step 2: MT5 Account Information")
    
    print("πŸ"' Enter your MT5 Account Details:")
    print("(You can find these in MetaTrader 5 Terminal)\n")
    
    # Get login
    while True:
        login_input = input("MT5 Account Number (LOGIN): ").strip()
        if login_input.isdigit() and 6 <= len(login_input) <= 10:
            login = login_input
            print_ok(f"Login: {login}")
            break
        else:
            print_error("Must be a 6-10 digit number (e.g., 433329124)")
    
    # Get password
    password = input("MT5 Password: ").strip()
    if not password:
        print_error("Password cannot be empty")
        return None
    print_ok(f"Password: {'*' * len(password)}")
    
    # Get server
    print("\nCommon servers:")
    print("  - Exness-MT5Trial")
    print("  - Exness-MT5")
    print("  - ThailandFutures-Demo")
    print()
    
    server = input("MT5 Server Name: ").strip()
    if not server:
        print_error("Server cannot be empty")
        return None
    print_ok(f"Server: {server}")
    
    return login, password, server


def test_mt5_connection(
    login: str,
    password: str,
    server: str,
    mt5_path: str
) -> bool:
    """Test MT5 connection."""
    print_header("Step 3: Testing MT5 Connection")
    
    try:
        import MetaTrader5 as mt5
        
        print("Attempting to connect to MT5...")
        
        # Initialize
        print(f"Initializing with path: {mt5_path}")
        if not mt5.initialize(path=mt5_path):
            code, msg = mt5.last_error()
            print_error(f"Initialize failed: {msg} ({code})")
            return False
        
        print_ok("MT5 initialized")
        
        # Login
        print(f"Logging in as {login} -> {server}...")
        if not mt5.login(int(login), password, server):
            code, msg = mt5.last_error()
            print_error(f"Login failed: {msg} ({code})")
            print_warn("Check:")
            print("  - Login number correct?")
            print("  - Password correct?")
            print("  - Server name correct?")
            mt5.shutdown()
            return False
        
        print_ok("Login successful!")
        
        # Get account info
        account = mt5.account_info()
        if account:
            print_ok(f"Account: {account.login}")
            print_ok(f"Balance: {account.balance}")
            print_ok(f"Equity: {account.equity}")
            print_ok(f"Trade Mode: {'DEMO' if account.trade_mode == 2 else 'LIVE' if account.trade_mode == 0 else f'OTHER({account.trade_mode})'}")
        
        # Get symbols
        symbols = mt5.symbols_get()
        if symbols:
            print_ok(f"Found {len(symbols)} symbols")
            print(f"  First few: {', '.join([s.name for s in symbols[:5]])}")
        
        # Shutdown
        mt5.shutdown()
        print_ok("Connection test successful!")
        return True
        
    except ImportError:
        print_error("MetaTrader5 package not installed")
        print("Install: pip install MetaTrader5")
        return False
    except Exception as e:
        print_error(f"Connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_env_file(login: str, password: str, server: str, mt5_path: str):
    """Update .env file with MT5 settings."""
    print_header("Step 4: Updating .env Configuration")
    
    env_file = Path(".env")
    if not env_file.exists():
        print_error(".env file not found")
        print("Creating from .env.example...")
        
        example_file = Path(".env.example")
        if example_file.exists():
            env_file.write_text(example_file.read_text())
            print_ok("Created .env from .env.example")
        else:
            print_error(".env.example not found either")
            return False
    
    # Read current env
    env_content = env_file.read_text(encoding='utf-8')
    
    # Update values
    lines = env_content.split('\n')
    new_lines = []
    
    for line in lines:
        if line.startswith('MT5_LOGIN='):
            new_lines.append(f'MT5_LOGIN={login}')
        elif line.startswith('MT5_PASSWORD='):
            new_lines.append(f'MT5_PASSWORD={password}')
        elif line.startswith('MT5_SERVER='):
            new_lines.append(f'MT5_SERVER={server}')
        elif line.startswith('MT5_PATH='):
            new_lines.append(f'MT5_PATH={mt5_path}')
        else:
            new_lines.append(line)
    
    # Write updated env
    env_file.write_text('\n'.join(new_lines), encoding='utf-8')
    
    print_ok("Updated .env file:")
    print(f"  MT5_LOGIN={login}")
    print(f"  MT5_PASSWORD={'*' * len(password)}")
    print(f"  MT5_SERVER={server}")
    print(f"  MT5_PATH={mt5_path}")
    
    return True


def verify_config() -> bool:
    """Verify config loads correctly."""
    print_header("Step 5: Verifying Configuration")
    
    try:
        from config import CONFIG
        
        print("Current MT5 Configuration:")
        print(f"  Login: {CONFIG.mt5_login}")
        print(f"  Server: {CONFIG.mt5_server}")
        print(f"  Path: {CONFIG.mt5_path}")
        
        if CONFIG.mt5_login and CONFIG.mt5_server and CONFIG.mt5_path:
            print_ok("Configuration looks good!")
            return True
        else:
            print_error("Some MT5 settings are missing")
            return False
            
    except Exception as e:
        print_error(f"Failed to load config: {e}")
        return False


def main():
    """Main setup flow."""
    print("\n" + "=" * 70)
    print("  PyTrade MT5 Connection Setup & Tester")
    print("=" * 70)
    print("\nThis tool will help you connect PyTrade to your MT5 account\n")
    
    # Step 1: Find MT5
    mt5_path = find_mt5_executable()
    if not mt5_path:
        print_error("Cannot proceed without MT5 Terminal")
        sys.exit(1)
    
    # Step 2: Get account info
    account_info = get_mt5_account_info()
    if not account_info:
        print_error("Account info required")
        sys.exit(1)
    
    login, password, server = account_info
    
    # Step 3: Test connection
    if not test_mt5_connection(login, password, server, mt5_path):
        print_warn("Connection test failed, but continuing...")
        response = input("\nContinue anyway? (y/n): ").strip().lower()
        if response != 'y':
            print_error("Setup cancelled")
            sys.exit(1)
    
    # Step 4: Update .env
    if not update_env_file(login, password, server, mt5_path):
        print_error("Failed to update .env")
        sys.exit(1)
    
    # Step 5: Verify
    verify_config()
    
    # Done
    print_header("✅ Setup Complete!")
    
    print("Next steps:")
    print("1. Your .env file is updated")
    print("2. Start PyTrade:")
    print("   python main.py --mode daemon")
    print("3. Open Dashboard:")
    print("   python -m streamlit run streamlit_app.py")
    print("\nFor issues, check MT5_CONNECTION_GUIDE.md")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
