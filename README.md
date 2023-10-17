# Group-Ten-Group-Smile
The terror of our times

[![Hippocratic License HL3-FULL](https://img.shields.io/static/v1?label=Hippocratic%20License&message=HL3-FULL&labelColor=5e2751&color=bc8c3d)](https://firstdonoharm.dev/version/3/0/full.html)

# Configuration & Running

## Environment Setup

**Python VENV:**

The following assumes the python executable is in your `PATH`, and may differ based on OS.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Environment Variables:**

The following should be included in a `.env` file in the root project directory.
```bash
# Database Configuration
DB_IP = 127.0.0.1 # Database IP
DB_PORT = 5432 # Database port [optional]
DB_USER = <username> # Database user
DB_PASSWORD = <password> # Database password
DB_DATABASE = p320_10 # Database name

# Database Tunnel Configuration
# If DB_TUNNEL is not provided, DB connection will be run in non-tunnelled mode.
# If the tunnel isn't active, all DB_TUNNEL_* variables are optional
DB_TUNNEL = true # Use SSH tunnel (true | false)
DB_TUNNEL_ADDR = starbug.cs.rit.edu # SSH tunnel address
DB_TUNNEL_PORT = 22 # SSH tunnel port [optional]
DB_TUNNEL_USERNAME = <username> # SSH tunnel username
DB_TUNNEL_PASSWORD = <password> # SSH tunnel password

# Debug Options
# All DEBUG_FLAG_* are optional, and false if omitted.
# If a flag is set to true, its arguments are potentially required
# If a flag is set to false, its arguments are ignored

DEBUG_FLAG_AUTOLOGIN = true # Automatically log in as a user
DEBUG_AUTOLOGIN_EMAIL = chesley_lesly@gmail.com
DEBUG_AUTOLOGIN_PASSWORD = tag-o$t-kager$

DEBUG_FLAG_AUTOTAB = true # Switch to panel tab upon login
DEBUG_AUTOTAB_NAME = books
```