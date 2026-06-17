#!/usr/bin/env bash
# Easee Domoticz plugin — install/update script for Domoticz (Debian)
# Usage:
#   ./install.sh              # clone or pull, then restart Domoticz
#   ./install.sh --no-restart   # skip Domoticz restart

set -euo pipefail

PLUGIN_DIR="/home/root/domoticz/plugins/Easee-Domoticz-plugin"
REPO_SSH="git@github.com:rleunk/easee-domoticz.git"
REPO_HTTPS="https://github.com/rleunk/easee-domoticz.git"
RESTART=true

for arg in "$@"; do
    case "$arg" in
        --no-restart) RESTART=false ;;
        -h|--help)
            echo "Usage: $0 [--no-restart]"
            echo "  Installs or updates the Easee Domoticz plugin via git."
            exit 0
            ;;
    esac
done

if [[ $EUID -ne 0 ]]; then
    echo "Tip: run as root if Domoticz runs under /home/root/ (sudo $0)"
fi

mkdir -p "$(dirname "$PLUGIN_DIR")"

if [[ -d "$PLUGIN_DIR/.git" ]]; then
    echo "==> Updating existing clone in $PLUGIN_DIR"
    git -C "$PLUGIN_DIR" pull --ff-only
elif [[ -d "$PLUGIN_DIR" ]]; then
    echo "ERROR: $PLUGIN_DIR exists but is not a git repository."
    echo "       Backup the folder, remove it, and run this script again."
    echo "       Or manually: cd $PLUGIN_DIR && git init && git remote add origin <url> && git pull"
    exit 1
else
    echo "==> Cloning repository into $PLUGIN_DIR"
    if ssh -o BatchMode=yes -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        git clone "$REPO_SSH" "$PLUGIN_DIR"
    else
        echo "SSH not configured — trying HTTPS (you may need username + PAT)."
        git clone "$REPO_HTTPS" "$PLUGIN_DIR"
    fi
fi

if [[ ! -f "$PLUGIN_DIR/plugin.py" ]]; then
    echo "ERROR: plugin.py not found in $PLUGIN_DIR"
    exit 1
fi

if [[ ! -f "$PLUGIN_DIR/Easee_icons_v2.zip" ]]; then
    echo "WARNING: Easee_icons_v2.zip not found in $PLUGIN_DIR"
    echo "         Custom icons will not load. Run: git -C \"$PLUGIN_DIR\" checkout HEAD -- Easee_icons_v2.zip"
else
    echo "==> Icon zip present: $PLUGIN_DIR/Easee_icons_v2.zip ($(stat -c%s "$PLUGIN_DIR/Easee_icons_v2.zip" 2>/dev/null || wc -c < "$PLUGIN_DIR/Easee_icons_v2.zip") bytes)"
    echo "    If tiles still show default icons after restart, upload the zip once via:"
    echo "    Domoticz → Setup → Settings → More Options → Custom Icons"
fi

echo "==> Plugin installed at $PLUGIN_DIR/plugin.py"

if $RESTART; then
    if systemctl is-active --quiet domoticz 2>/dev/null; then
        echo "==> Restarting Domoticz..."
        systemctl restart domoticz
        echo "==> Done. Check Domoticz → Setup → Hardware."
    else
        echo "==> Domoticz service not found via systemctl."
        echo "    Restart Domoticz manually, then enable the plugin in Setup → Hardware."
    fi
else
    echo "==> Skipped Domoticz restart (--no-restart)."
fi
