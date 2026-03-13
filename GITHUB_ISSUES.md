# GitHub Issues for Strava Commute Route Analyzer

This document contains GitHub issues for outstanding tasks and improvements.

---

## Issue #6: ✅ RESOLVED - Fix Logger Reference Before Definition

**Labels:** `bug`, `priority: critical`, `resolved`

**Title:** Logger referenced before definition in route_analyzer.py

**Description:**

VSCode identified a critical bug where the `logger` variable was being referenced in an exception handler before it was defined, which would cause a `NameError` at runtime if the `similaritymeasures` package was not installed.

### Problem:

In `src/route_analyzer.py`, the code attempted to use `logger.warning()` in the `except ImportError` block (line 24) before `logger` was initialized (line 30):

```python
try:
    import similaritymeasures
    FRECHET_AVAILABLE = True
except ImportError:
    FRECHET_AVAILABLE = False
    logger.warning("...")  # ❌ NameError: logger not defined yet
    
logger = logging.getLogger(__name__)  # Defined here
```

### Solution:

Moved the logger initialization before the try-except block to ensure it's available when needed:

```python
logger = logging.getLogger(__name__)  # ✅ Define first

try:
    import similaritymeasures
    FRECHET_AVAILABLE = True
except ImportError:
    FRECHET_AVAILABLE = False
    logger.warning("...")  # ✅ Now works correctly
```

### Resolution:

- **Fixed in commit:** `7423f0d`
- **Files changed:** `src/route_analyzer.py`
- **Documentation:** `VSCODE_PROBLEMS_RESOLUTION.md`
- **Status:** ✅ RESOLVED

### Validation:

- ✅ All Python files pass syntax validation
- ✅ AST parsing successful for all modules
- ✅ No runtime errors when similaritymeasures is missing
- ✅ Logger properly initialized before use

**Closed:** 2026-03-13

---

## Issue #1: Test Interactive Route Highlighting Features

**Labels:** `testing`, `enhancement`, `priority: high`

**Title:** Test and validate interactive route highlighting in HTML report

**Description:**

The interactive route highlighting features have been implemented but need comprehensive testing to ensure they work correctly across different browsers and scenarios.

### Features to Test:

1. **Hover Highlighting**
   - Hover over route names in the comparison table
   - Verify route is highlighted on the map
   - Verify other routes are dimmed
   - Test that highlighting resets when mouse leaves

2. **Click to Persist**
   - Click on a route name to keep it highlighted
   - Verify route stays highlighted when mouse moves away
   - Click again to deselect
   - Verify routes return to normal state

3. **Map Interaction**
   - Verify map displays correctly in right pane
   - Test sticky positioning of map during scroll
   - Verify route colors match between table and map
   - Test popup information on route click

4. **Cross-browser Testing**
   - Chrome/Edge
   - Firefox
   - Safari
   - Mobile browsers

### Testing Steps:

1. Run the analyzer with real Strava data:
   ```bash
   cd commute
   python3 main.py --analyze
   ```

2. Open the generated report in `output/reports/commute_analysis.html`

3. Test each feature listed above

4. Document any issues found

### Acceptance Criteria:

- [ ] Hover highlighting works smoothly without lag
- [ ] Click to persist works correctly
- [ ] Routes can be selected and deselected
- [ ] Map displays correctly in right pane
- [ ] No JavaScript errors in browser console
- [ ] Works in major browsers (Chrome, Firefox, Safari)
- [ ] Mobile responsive design works

### Notes:

The JavaScript implementation uses direct DOM manipulation to highlight routes. If the Folium map structure changes, the selectors may need updating.

---

## Issue #2: Enhance Route Naming with Real Geocoding

**Labels:** `enhancement`, `feature`, `priority: medium`

**Title:** Implement full geocoding for route names based on streets

**Description:**

Currently, route names use simple naming (e.g., "Primary Route to Work"). The `RouteNamer` class has been created with geocoding support, but it needs to be fully integrated and tested.

### Current State:

- `RouteNamer` class exists in `src/route_namer.py`
- Has methods for reverse geocoding using Nominatim
- Currently using simple naming as fallback
- Geocoding is rate-limited and requires internet

### Tasks:

1. **Enable Geocoding by Default**
   - Add configuration option to enable/disable geocoding
   - Implement proper error handling for offline scenarios
   - Add caching for geocoded street names

2. **Improve Street Name Selection**
   - Sample more strategic points along routes
   - Prioritize major streets over minor ones
   - Handle cases where street names aren't available

3. **Add Configuration Options**
   ```yaml
   route_naming:
     enable_geocoding: true
     cache_geocoding: true
     max_retries: 3
     timeout_seconds: 5
     sample_points: 3
   ```

4. **Testing**
   - Test with various route types
   - Test offline behavior
   - Test rate limiting handling
   - Verify cache works correctly

### Example Output:

Instead of "Route 1 to Work", generate names like:
- "Via Michigan Ave → Lake Shore Dr"
- "Clark St → Division St Route"
- "Lakeshore Path Route"

### Acceptance Criteria:

- [ ] Geocoding can be enabled via config
- [ ] Street names are cached to avoid repeated API calls
- [ ] Graceful fallback to simple names when geocoding fails
- [ ] Rate limiting is handled properly
- [ ] Works offline with cached data
- [ ] Documentation updated with examples

---

## Issue #3: Improve Map-Table Synchronization

**Labels:** `enhancement`, `bug`, `priority: medium`

**Title:** Enhance JavaScript for better map-table interaction

**Description:**

The current JavaScript implementation for highlighting routes may not work perfectly with all Folium map configurations. Need to improve the synchronization between table interactions and map highlighting.

### Known Issues:

1. **Folium Map Access**
   - Current implementation tries to access map elements directly
   - May not work if Folium changes its HTML structure
   - Need more robust way to identify and highlight routes

2. **Route Identification**
   - Routes need unique identifiers that persist in both table and map
   - Current className approach may not be reliable

### Proposed Solutions:

1. **Add Data Attributes to Folium Routes**
   - Modify `visualizer.py` to add custom data attributes
   - Use these for reliable route identification
   - Example: `data-route-id="home_to_work_0"`

2. **Improve JavaScript Selectors**
   - Use more specific selectors
   - Add fallback methods for route identification
   - Better error handling

3. **Add Visual Feedback**
   - Show loading state while map initializes
   - Add tooltips explaining interaction
   - Highlight selected route in table with icon

### Implementation:

```python
# In visualizer.py, when creating polylines:
folium.PolyLine(
    coords,
    color=color,
    weight=weight,
    opacity=opacity,
    popup=popup_html,
    tooltip=route_name,
    className=f"route-line route-{route_group.id}",
    # Add custom attributes
    **{'data-route-id': route_group.id}
).add_to(self.map)
```

### Acceptance Criteria:

- [ ] Routes can be reliably identified in map
- [ ] Highlighting works consistently
- [ ] No console errors
- [ ] Visual feedback for user interactions
- [ ] Works with different Folium versions

---

## Issue #4: Add Route Comparison Metrics Visualization

**Labels:** `enhancement`, `feature`, `priority: low`

**Title:** Add charts and graphs for route comparison

**Description:**

Enhance the report with visual comparisons of routes using charts.

### Proposed Features:

1. **Bar Charts**
   - Compare duration across routes
   - Compare distance across routes
   - Compare elevation gain

2. **Radar Chart**
   - Show multi-dimensional comparison
   - Include time, distance, safety, consistency

3. **Time Series**
   - Show route usage over time
   - Identify seasonal patterns

### Implementation:

- Use Chart.js or similar library
- Add charts below route comparison table
- Make charts interactive (click to highlight route)

### Acceptance Criteria:

- [ ] Charts display correctly
- [ ] Charts are interactive
- [ ] Charts are responsive
- [ ] Data is accurate

---

## Issue #5: Mobile Responsive Design Improvements

**Labels:** `enhancement`, `ui/ux`, `priority: medium`

**Title:** Improve mobile experience for HTML report

**Description:**

The current report layout with side-by-side comparison and map may not work well on mobile devices.

### Tasks:

1. **Responsive Layout**
   - Stack table and map vertically on mobile
   - Adjust map height for mobile
   - Make table scrollable horizontally if needed

2. **Touch Interactions**
   - Ensure hover effects work with touch
   - Add tap-to-highlight for mobile
   - Improve button sizes for touch

3. **Performance**
   - Lazy load map on mobile
   - Optimize JavaScript for mobile browsers

### Acceptance Criteria:

- [ ] Report is usable on mobile devices
- [ ] All interactions work with touch
- [ ] Layout adapts to screen size
- [ ] Performance is acceptable on mobile

## Issue #7: Containerize Application with Podman Support

**Labels:** `enhancement`, `feature`, `infrastructure`, `priority: high`

**Title:** Add containerization support for Podman/Docker deployment

**Description:**

Containerize the application to enable easy deployment, consistent environments, and better portability. Support both Docker and Podman (rootless container runtime).

### Requirements:

1. **Dockerfile Creation**
   - Base image: Python 3.11+ slim
   - Install all dependencies from requirements.txt
   - Set up proper working directory
   - Configure environment variables
   - Expose necessary ports (if web interface added later)

2. **Podman Compatibility**
   - Ensure Dockerfile works with both Docker and Podman
   - Test rootless Podman deployment
   - Document Podman-specific commands

3. **Volume Mounts**
   - `/app/cache` - For geocoding and weather cache
   - `/app/data` - For activity data storage
   - `/app/output` - For generated reports
   - `/app/config` - For configuration files
   - `/app/.env` - For environment variables (secrets)

4. **Docker Compose / Podman Compose**
   - Create compose file for easy deployment
   - Configure volume mounts
   - Set environment variables
   - Add health checks

### Implementation:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p cache data output config

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python3", "main.py", "--analyze"]
```

```yaml
# docker-compose.yml / podman-compose.yml
version: '3.8'

services:
  strava-analyzer:
    build: .
    container_name: strava-route-analyzer
    volumes:
      - ./cache:/app/cache
      - ./data:/app/data
      - ./output:/app/output
      - ./config:/app/config
      - ./.env:/app/.env:ro
    environment:
      - STRAVA_CLIENT_ID=${STRAVA_CLIENT_ID}
      - STRAVA_CLIENT_SECRET=${STRAVA_CLIENT_SECRET}
    restart: unless-stopped
```

### Testing:

```bash
# Docker
docker build -t strava-analyzer .
docker run -v $(pwd)/cache:/app/cache -v $(pwd)/.env:/app/.env strava-analyzer

# Podman
podman build -t strava-analyzer .
podman run -v $(pwd)/cache:/app/cache:Z -v $(pwd)/.env:/app/.env:ro,Z strava-analyzer
```

### Acceptance Criteria:

- [ ] Dockerfile builds successfully
- [ ] Works with both Docker and Podman
- [ ] All dependencies installed correctly
- [ ] Volume mounts work properly
- [ ] Environment variables passed correctly
- [ ] Cache persists between runs
- [ ] Documentation includes container usage
- [ ] Compose file provided for easy deployment

---

## Issue #8: Add Multi-User Support with Strava OAuth

**Labels:** `enhancement`, `feature`, `security`, `priority: high`

**Title:** Implement multi-user system with individual Strava authentication

**Description:**

Transform the single-user CLI application into a multi-user system where each user can authenticate with their own Strava account and view their personal cycling data.

### Architecture Changes:

1. **User Management System**
   - User registration/login system
   - Store user credentials securely (hashed passwords)
   - User session management
   - User profile management

2. **Per-User Strava Authentication**
   - Each user authenticates with their own Strava account
   - Store OAuth tokens per user (encrypted)
   - Handle token refresh per user
   - Support multiple Strava accounts per user (optional)

3. **Data Isolation**
   - Separate data storage per user
   - User-specific cache directories
   - User-specific output directories
   - Prevent cross-user data access

4. **Web Interface** (Required for multi-user)
   - Flask or FastAPI web framework
   - Login/logout functionality
   - Dashboard showing user's routes
   - Interactive report viewing
   - Settings page for user preferences

### Database Schema:

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Strava tokens table
CREATE TABLE strava_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    access_token TEXT NOT NULL,  -- Encrypted
    refresh_token TEXT NOT NULL,  -- Encrypted
    expires_at TIMESTAMP NOT NULL,
    athlete_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- User settings table
CREATE TABLE user_settings (
    user_id INTEGER PRIMARY KEY,
    home_lat REAL,
    home_lon REAL,
    work_lat REAL,
    work_lon REAL,
    config_yaml TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Directory Structure:

```
/app/
  /users/
    /user_123/
      /cache/
      /data/
      /output/
      /config/
```

### Security Requirements:

- Password hashing with bcrypt or argon2
- OAuth tokens encrypted at rest
- HTTPS required for production
- CSRF protection
- Rate limiting on API endpoints
- Session timeout
- Secure cookie handling

### Acceptance Criteria:

- [ ] User registration and login system
- [ ] Per-user Strava OAuth flow
- [ ] Data isolation between users
- [ ] Web interface for user interaction
- [ ] Secure token storage (encrypted)
- [ ] Session management
- [ ] User can only access their own data
- [ ] Admin interface for user management (optional)

---

## Issue #9: Implement Security and Access Control

**Labels:** `security`, `priority: critical`

**Title:** Ensure robust security and user access control

**Description:**

Implement comprehensive security measures to protect user data and ensure proper access control in the multi-user system.

### Security Requirements:

1. **Authentication Security**
   - Strong password requirements (min 12 chars, complexity)
   - Password hashing with bcrypt (cost factor 12+)
   - Account lockout after failed login attempts
   - Two-factor authentication (optional, future)
   - Secure password reset flow

2. **Authorization & Access Control**
   - Role-based access control (RBAC)
   - User can only access their own data
   - Admin role for system management
   - API endpoint authorization checks
   - File system permission checks

3. **Data Protection**
   - Encrypt sensitive data at rest (OAuth tokens, API keys)
   - Use environment variables for secrets
   - Secure key management (consider HashiCorp Vault)
   - Regular security audits
   - Data retention policies

4. **Network Security**
   - HTTPS/TLS required in production
   - Secure headers (HSTS, CSP, X-Frame-Options)
   - CORS configuration
   - Rate limiting to prevent abuse
   - DDoS protection considerations

5. **Input Validation**
   - Sanitize all user inputs
   - Validate file uploads
   - Prevent SQL injection (use parameterized queries)
   - Prevent XSS attacks
   - Validate OAuth callbacks

6. **Audit Logging**
   - Log all authentication attempts
   - Log data access events
   - Log configuration changes
   - Log failed authorization attempts
   - Secure log storage

### Implementation:

```python
# Example: User data access control
def get_user_data(user_id: int, requested_user_id: int):
    """Ensure user can only access their own data."""
    if user_id != requested_user_id:
        raise PermissionError("Access denied: Cannot access other user's data")
    
    # Proceed with data retrieval
    return fetch_data(requested_user_id)

# Example: File system isolation
def get_user_directory(user_id: int) -> Path:
    """Get user-specific directory with proper permissions."""
    user_dir = Path(f"/app/users/user_{user_id}")
    user_dir.mkdir(mode=0o700, exist_ok=True)  # Owner only
    return user_dir
```

### Security Checklist:

- [ ] Password hashing implemented (bcrypt/argon2)
- [ ] OAuth tokens encrypted at rest
- [ ] HTTPS enforced in production
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output escaping)
- [ ] Secure session management
- [ ] File system permissions properly set
- [ ] Audit logging implemented
- [ ] Security headers configured
- [ ] Secrets stored in environment variables
- [ ] Regular dependency updates (security patches)
- [ ] Security testing performed

### Compliance Considerations:

- GDPR compliance (if serving EU users)
- Data export functionality
- Data deletion functionality
- Privacy policy
- Terms of service

### Acceptance Criteria:

- [ ] All security measures implemented
- [ ] Security audit passed
- [ ] Penetration testing completed
- [ ] Documentation includes security best practices
- [ ] Incident response plan documented

---

## Priority Summary

**Critical Priority:**
- Issue #9: Implement Security and Access Control

**High Priority:**
- Issue #1: Test Interactive Features
- Issue #7: Containerize Application with Podman Support
- Issue #8: Add Multi-User Support with Strava OAuth

**Medium Priority:**
- Issue #2: Enhance Route Naming
- Issue #3: Improve Map-Table Sync
- Issue #5: Mobile Responsive Design

**Low Priority:**
- Issue #4: Add Charts/Graphs

**Resolved:**
- Issue #6: ✅ Fix Logger Reference Before Definition (Commit: 7423f0d)

---

## How to Create These Issues on GitHub

1. Go to your repository on GitHub
2. Click on "Issues" tab
3. Click "New Issue"
4. Copy the title and description from each issue above
5. Add the appropriate labels
6. Assign to yourself or team members
7. Add to project board if using one

---

*Generated: 2026-03-13*