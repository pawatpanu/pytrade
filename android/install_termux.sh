#!/data/data/com.termux/files/usr/bin/bash
# PyTrade Termux Installation Script
# For running PyTrade on Android via Termux
# 
# Usage: bash install_termux.sh
#
# Requirements:
# - Termux app (from F-Droid or Play Store)
# - ~2GB free space
# - WiFi connection
#

set -e

echo "============================================"
echo "πŸ€ PyTrade Termux Installation"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${GREEN}βœ… $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================
# Step 1: Update system
# ============================================
echo "Step 1: Updating Termux packages..."
pkg update -y > /dev/null 2>&1
pkg upgrade -y > /dev/null 2>&1
print_status "Termux updated"
echo ""

# ============================================
# Step 2: Install dependencies
# ============================================
echo "Step 2: Installing dependencies..."
print_warning "This may take several minutes..."
echo ""

# System packages
echo "  Installing system packages..."
pkg install -y git python python-pip clang libffi openssl > /dev/null 2>&1
print_status "System packages installed"

# Python packages
echo "  Installing Python packages..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
print_status "Python tools upgraded"
echo ""

# ============================================
# Step 3: Clone PyTrade repository
# ============================================
echo "Step 3: Setting up PyTrade..."
PYTRADE_DIR="$HOME/pytrade"

if [ -d "$PYTRADE_DIR" ]; then
    print_warning "PyTrade directory already exists"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing installation"
        PYTRADE_DIR="$PYTRADE_DIR"_new
    else
        rm -rf "$PYTRADE_DIR"
    fi
fi

# Clone repo
echo "  Cloning PyTrade repository..."
cd "$HOME"
git clone https://github.com/pawatpanu/pytrade.git "$PYTRADE_DIR" 2>/dev/null
print_status "PyTrade cloned to $PYTRADE_DIR"
echo ""

# ============================================
# Step 4: Install Python requirements
# ============================================
echo "Step 4: Installing Python requirements..."
cd "$PYTRADE_DIR"

# Install MetaTrader5 (if available for this platform)
echo "  Installing core packages..."
pip install -q \
    pandas numpy ta streamlit \
    python-dotenv requests schedule \
    pyzmq --upgrade > /dev/null 2>&1

# Try to install MetaTrader5 (might not work on Termux)
echo "  Attempting MetaTrader5 installation..."
pip install -q MetaTrader5 2>/dev/null || print_warning "MT5 not available (requires PC bridge)"
print_status "Python packages installed"
echo ""

# ============================================
# Step 5: Create virtual environment (optional)
# ============================================
echo "Step 5: Virtual environment setup..."
if [ -d "$PYTRADE_DIR/venv" ]; then
    print_warning "Virtual environment already exists"
else
    python -m venv "$PYTRADE_DIR/venv"
    print_status "Virtual environment created"
fi
echo ""

# ============================================
# Step 6: Configure for Android
# ============================================
echo "Step 6: Configuring for Android..."

# Create .env for Android
if [ ! -f "$PYTRADE_DIR/.env.android" ]; then
    cat > "$PYTRADE_DIR/.env.android" << 'EOF'
# Android MT5 Connection (must be bridged from PC)
MT5_LOGIN=
MT5_PASSWORD=
MT5_SERVER=
MT5_PATH=

# Connection to PC PyTrade instance
PYTRADE_HOST=192.168.1.100
PYTRADE_PORT=8501
PYTRADE_MODE=dashboard_only

# Symbols
SYMBOLS=BTCUSD,ETHUSD

TIMEFRAME_PRIMARY=H4
TIMEFRAME_CONFIRM=H1

# Dashboard
STREAMLIT_THEME_BASE=dark
STREAMLIT_LOGGER_LEVEL=info

# Android-specific
ANDROID_MODE=true
ANDROID_HEADLESS=false
EOF
    print_status ".env.android created"
fi
echo ""

# ============================================
# Step 7: Create startup scripts
# ============================================
echo "Step 7: Creating startup scripts..."

# Dashboard script
cat > "$PYTRADE_DIR/start_dashboard_android.sh" << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/pytrade"
source venv/bin/activate
python -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
EOF
chmod +x "$PYTRADE_DIR/start_dashboard_android.sh"
print_status "Dashboard startup script created"

# Connection check script
cat > "$PYTRADE_DIR/check_connection.py" << 'EOF'
#!/usr/bin/env python3
import socket
import sys

def check_server(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"✓ Connected to {host}:{port}")
            return True
        else:
            print(f"✗ Cannot reach {host}:{port}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8501
    sys.exit(0 if check_server(host, port) else 1)
EOF
chmod +x "$PYTRADE_DIR/check_connection.py"
print_status "Connection check script created"
echo ""

# ============================================
# Step 8: Final instructions
# ============================================
echo ""
echo "============================================"
print_status "Installation Complete!"
echo "============================================"
echo ""

echo "πŸ" NEXT STEPS:"
echo "1. Edit .env.android in $PYTRADE_DIR"
echo "2. Set PYTRADE_HOST to your PC IP"
echo "3. Run: $PYTRADE_DIR/start_dashboard_android.sh"
echo ""

echo "πŸ"— USEFUL COMMANDS:"
echo "  Start Dashboard:"
echo "    bash $PYTRADE_DIR/start_dashboard_android.sh"
echo ""
echo "  Check PC Connection:"
echo "    python $PYTRADE_DIR/check_connection.py 192.168.1.100 8501"
echo ""
echo "  Find your Android IP:"
echo "    ifconfig"
echo ""

echo "πŸ" IMPORTANT NOTES:"
echo "  β€' MT5 requires PC bridge (cannot run directly on Android)"
echo "  β€' This installation is for Dashboard/Monitoring only"
echo "  β€' Real trading must happen on PT with MT5 Terminal"
echo "  β€' Keep PC PyTrade daemon running"
echo ""

echo "βš™οΈ  TROUBLESHOOTING:"
echo "  Cannot connect to PC?"
echo "  1. Verify same WiFi network"
echo "  2. Check PC firewall allows port 8501"
echo "  3. Verify PC IP in .env.android"
echo "  4. Run: python check_connection.py <PC-IP>"
echo ""

print_status "Setup finished! Enjoy PyTrade on Termux πŸ€"
