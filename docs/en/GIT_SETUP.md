# Git authentication on the Domoticz server

**Language:** **English** · [Nederlands](../GIT_SETUP.md)

GitHub no longer accepts account passwords for HTTPS since August 2021. Use a **Personal Access Token (PAT)** or SSH.

## HTTPS clone (default)

```bash
cd /home/USER/domoticz/plugins
git clone https://github.com/rleunk/easee-domoticz.git Easee-Domoticz-plugin
cd Easee-Domoticz-plugin
git checkout main
```

Folder name **`Easee-Domoticz-plugin`** is required — Domoticz expects `plugin.py` in that folder.

### Updates

```bash
cd /home/USER/domoticz/plugins/Easee-Domoticz-plugin
git pull
sudo systemctl restart domoticz
```

## HTTPS with Personal Access Token

1. Create token: [GitHub → Settings → Developer settings → Tokens](https://github.com/settings/tokens) — scope **repo**
2. When prompted: username `rleunk`, password = **PAT** (not GitHub password)
3. Optional: `git config --global credential.helper store` to save credentials

## SSH (optional)

```bash
ssh-keygen -t ed25519 -C "domoticz-easee" -f ~/.ssh/id_ed25519_github -N ""
cat ~/.ssh/id_ed25519_github.pub   # add to GitHub SSH keys
git clone git@github.com:rleunk/easee-domoticz.git Easee-Domoticz-plugin
```

## Common errors

| Error | Fix |
|-------|-----|
| `Password authentication is not supported` | Use PAT or SSH |
| `Permission denied (publickey)` | Add SSH key to GitHub |
| `Repository not found` | Check URL and access |
| `not a git repository` | `cd` to plugin folder |

## Folder layout after clone

```
Easee-Domoticz-plugin/
├── plugin.py
├── easee_i18n.py          ← v1.1.6+ (NL/EN UI)
├── pricing/               ← v1 price sources
├── Easee_icons_v2.zip
└── docs/en/               ← English documentation
```

See [INSTALL.en.md](../../INSTALL.en.md) for Domoticz setup.
