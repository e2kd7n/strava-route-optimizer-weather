# Strava Authentication Guide

## Two Authentication Methods

### Method 1: OAuth Flow (Recommended for New Users)
**What you need:**
- Client ID
- Client Secret

**How to get them:**
1. Go to https://www.strava.com/settings/api
2. Click "Create an App" or use existing app
3. Fill in:
   - **Application Name:** Commute Analyzer
   - **Category:** Data Importer
   - **Website:** http://localhost
   - **Authorization Callback Domain:** `localhost` (exactly this, no http://)
4. Copy your Client ID and Client Secret

**Setup:**
```bash
# .env file
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
```

**Run:**
```bash
python3 main.py --auth
```

This will:
1. Open your browser
2. Ask you to authorize the app
3. Save tokens automatically
4. Refresh tokens when they expire

---

### Method 2: Direct Access Token (Quick Start)
**What you need:**
- Access Token (from Strava API page)

**How to get it:**
1. Go to https://www.strava.com/settings/api
2. Scroll down to "Your Access Token"
3. Copy the token shown there

**Setup:**
```bash
# .env file
STRAVA_ACCESS_TOKEN=your_access_token_here
```

**Note:** This token:
- ✅ Works immediately, no OAuth needed
- ❌ Expires after 6 hours
- ❌ Cannot be refreshed automatically
- ⚠️ Only for testing/development

---

## Which Method Should You Use?

### Use OAuth Flow (Method 1) if:
- ✅ You want long-term use
- ✅ You want automatic token refresh
- ✅ You're building for production

### Use Access Token (Method 2) if:
- ✅ You just want to test quickly
- ✅ You're debugging
- ✅ You don't mind re-authenticating every 6 hours

---

## Current Issue: Invalid Credentials

The error you're seeing means:
```
Authorization Error: [{'resource': 'Application', 'field': '', 'code': 'invalid'}]
```

**This happens when:**
1. Client ID doesn't exist
2. Client Secret doesn't match the Client ID
3. The Strava app was deleted
4. Authorization Callback Domain is wrong

**To fix:**
1. Go to https://www.strava.com/settings/api
2. Verify your app exists
3. Check "Authorization Callback Domain" is exactly: `localhost`
4. Copy the EXACT Client ID and Client Secret
5. Update .env file

---

## Quick Test with Access Token

If you want to test the app immediately:

1. Get your access token from https://www.strava.com/settings/api
2. Create a simple test script:

```python
# test_token.py
from stravalib.client import Client

token = "your_access_token_here"
client = Client(access_token=token)

# Test it
athlete = client.get_athlete()
print(f"Connected as: {athlete.firstname} {athlete.lastname}")

# Get activities
activities = list(client.get_activities(limit=5))
print(f"Found {len(activities)} activities")
```

3. Run it:
```bash
python3 test_token.py
```

If this works, your token is valid and you can use Method 2 for quick testing.

---

## Recommended Setup Process

1. **First, test with access token** (Method 2) to verify everything works
2. **Then, set up OAuth** (Method 1) for long-term use

This way you can confirm the app works before dealing with OAuth setup.