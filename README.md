# Strava Commute Route Analyzer

A Python application that analyzes your Strava cycling activities to determine the optimal commute route between home and work, considering time, distance, and safety factors.

## 🔒 Security Notice

**This application requires valid Strava API credentials to run.** The program will not execute without proper authentication credentials configured in your `.env` file. This protects against unauthorized use and ensures the application only runs for legitimate users with their own Strava API access.

If you encounter this project hosted elsewhere without proper attribution or with modifications that bypass authentication, please report it as it violates the terms of use.

## Features

### Commute Analysis
- 🔍 **Automatic Location Detection**: Identifies your home and work locations from activity patterns
- 📊 **Multi-Criteria Analysis**: Evaluates routes based on time, distance, safety, and weather
- 🧮 **Advanced Route Matching**: Uses Fréchet distance algorithm for accurate path similarity detection
- 🏷️ **Intelligent Route Naming**: Segment-based naming shows complete journey (e.g., "Wells St → Lakefront Trail → North Ave")
- 🌤️ **Real-Time Weather Analysis**: Considers wind speed and direction for optimal route selection
- 🎯 **Personalized Recommendations**: Suggests optimal routes based on your preferences and current conditions

### Long Rides Analysis (NEW in v2.4.0)
- 🚵 **Comprehensive Statistics**: View total rides, average distance, longest ride, elevation gain, and more
- 🏆 **Top 10 Longest Rides**: Table with Strava links showing your most epic adventures
- 📅 **Monthly Breakdown**: Chart showing ride count and distance trends over time
- 🗺️ **Interactive Map**: Visualize all your long rides (>15km) with color-coded routes by distance
- 🔄 **Route Filtering**: Filter between loops and point-to-point rides
- 📈 **Detailed Metrics**: Speed, elevation, duration, and route type for each ride

### General Features
- 🗺️ **Interactive Maps**: Generates beautiful HTML reports with interactive route visualizations
- ⚡ **Smart Caching**: Minimizes API calls by caching activity data locally
- 📱 **Mobile Responsive**: Works seamlessly on desktop, tablet, and mobile devices

## How It Works

1. **Fetches Your Activities**: Retrieves your cycling activities from Strava
2. **Identifies Locations**: Uses clustering algorithms to find your home and work locations
3. **Analyzes Routes**: Groups similar routes and calculates detailed metrics
4. **Optimizes Selection**: Scores routes based on time, distance, and safety factors
5. **Generates Report**: Creates an interactive HTML report with maps and recommendations

## Prerequisites

- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **pip** (Python package installer) - Usually included with Python
- **Git** (optional, for cloning) - [Download Git](https://git-scm.com/downloads)
- A **Strava account** with cycling activities
- **Strava API credentials** (free to obtain - instructions below)

### Checking Your Python Installation

Before starting, verify Python is installed:

```bash
# Check Python version (should be 3.8 or higher)
python3 --version

# Or on Windows:
python --version

# Check pip is installed
pip --version
```

If Python is not installed, download it from [python.org](https://www.python.org/downloads/) and follow the installation instructions for your operating system.

## Installation

### 1. Clone or Download the Repository

**Option A: Using Git (Recommended)**
```bash
git clone https://github.com/yourusername/ride-optimizer.git
cd ride-optimizer
```

**Option B: Download ZIP**
1. Download the repository as a ZIP file from GitHub
2. Extract it to a folder (e.g., `~/ride-optimizer` or `C:\Users\YourName\ride-optimizer`)
3. Open a terminal/command prompt and navigate to that folder:
   ```bash
   cd ~/ride-optimizer  # macOS/Linux
   cd C:\Users\YourName\ride-optimizer  # Windows
   ```

### 2. Create Virtual Environment

A virtual environment keeps this project's dependencies separate from other Python projects.

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

You should see `(venv)` appear at the start of your command prompt, indicating the virtual environment is active.

### 3. Install Dependencies

With the virtual environment activated, install all required packages:

```bash
pip install -r requirements.txt
```

This will install all necessary Python packages including:
- `stravalib` - Strava API client
- `folium` - Interactive maps
- `pandas` - Data analysis
- `scikit-learn` - Machine learning algorithms
- `geopy` - Geocoding
- And other dependencies

**Troubleshooting Installation:**
- If you get permission errors, make sure your virtual environment is activated
- On macOS/Linux, you may need to install system dependencies first:
  ```bash
  # macOS (using Homebrew)
  brew install python3
  
  # Ubuntu/Debian
  sudo apt-get update
  sudo apt-get install python3 python3-pip python3-venv
  ```
- On Windows, if you get SSL errors, try:
  ```bash
  pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
  ```

### 4. Get Strava API Credentials (REQUIRED)

**⚠️ The application will not run without valid Strava API credentials.**

1. Go to https://www.strava.com/settings/api
2. Create a new application:
   - **Application Name**: Commute Analyzer (or any name)
   - **Category**: Data Importer
   - **Website**: http://localhost
   - **Authorization Callback Domain**: localhost
3. Note your **Client ID** and **Client Secret**

### 5. Configure Environment (REQUIRED)

Create a `.env` file in the project root with your actual credentials:

```bash
STRAVA_CLIENT_ID=your_actual_client_id
STRAVA_CLIENT_SECRET=your_actual_client_secret
```

**Important:**
- Replace `your_actual_client_id` and `your_actual_client_secret` with your real credentials
- The application validates credentials at startup and will exit if they are missing or invalid
- Never share your `.env` file or commit it to version control

## Quick Start

### First Time Setup

1. **Authenticate with Strava**:
```bash
python main.py --auth
```
This will open your browser for OAuth authorization. After granting access, the tokens will be saved locally.

2. **Run Analysis**:
```bash
python main.py --analyze
```

This will:
- Fetch your activities from Strava
- Identify your home and work locations
- Analyze all commute routes
- Generate an interactive HTML report

3. **View Results**:
Open `output/reports/commute_analysis.html` in your browser.

## Usage

### Performance Options

**Parallel Processing** (New!)
The analyzer now supports parallel processing for faster route grouping:

```bash
# Use default 2 workers
python main.py --analyze

# Use 4 workers for faster processing
python main.py --analyze --parallel 4

# Use maximum 8 workers
python main.py --analyze --parallel 8
```

Parallel processing provides ~1.5-2x speedup when analyzing large numbers of routes. The `--parallel` flag accepts values from 1-8 (default: 2).

### Basic Commands

```bash
# Authenticate with Strava (first time only)
python main.py --auth

# Show cached activity statistics
python main.py --stats

# Fetch new activities and update cache (merges with existing)
python main.py --fetch

# Run full analysis and generate report
python main.py --analyze

# Fetch and analyze in one command
python main.py --fetch --analyze
```

### Data Fetching Options

The `--fetch` command now supports flexible data retrieval with automatic cache merging:

```bash
# Fetch most recent 100 activities
python main.py --fetch --limit 100

# Fetch activities from a specific date onwards
python main.py --fetch --from-date 2023-01-01

# Fetch ALL activities within a date range (ignores --limit)
python main.py --fetch --from-date 2023-01-01 --to-date 2023-12-31

# Fetch specific number from a date
python main.py --fetch --from-date 2024-01-01 --limit 200

# Replace cache completely (WARNING: loses existing data)
python main.py --fetch --replace-cache
```

**Cache Behavior:**
- By default, `--fetch` **merges** new activities with existing cache
- Duplicates are automatically detected and updated
- Historical data is preserved across fetches
- Use `--replace-cache` only when you want to start fresh

**Smart Limit Handling:**
- When both `--from-date` and `--to-date` are specified, ALL activities in that range are fetched
- The `--limit` parameter is ignored for date ranges to ensure complete data
- Without date range, `--limit` controls how many recent activities to fetch (default: 500)

### Cache Statistics

View detailed statistics about your cached activities:

```bash
python main.py --stats
```

Shows:
- Total activities and cache timestamp
- Date range (earliest to latest activity)
- Activity types breakdown
- Commute activity counts (to work, from work)
- Distance and duration statistics

### Advanced Options

```bash
# Use custom configuration file
python main.py --analyze --config my_config.yaml

# Specify output directory
python main.py --analyze --output ~/Desktop/reports

# Combine options
python main.py --fetch --from-date 2023-01-01 --analyze --output ./my_reports
```

### 📱 Mobile Usage

The generated HTML report is mobile-friendly! You can transfer it to your phone and view it there. Weather data will update automatically when you have an internet connection.

**See [MOBILE_USAGE_GUIDE.md](MOBILE_USAGE_GUIDE.md) for detailed instructions on:**
- How to transfer the report to your phone (AirDrop, email, cloud storage, USB)
- Opening and viewing on iPhone or Android
- What features work offline vs. require internet
- Troubleshooting tips

```

## Configuration

Edit `config/config.yaml` to customize the analysis:

### Optimization Weights

Adjust how routes are scored:

```yaml
optimization:
  weights:
    time: 0.25      # Speed and duration
    distance: 0.10  # Route length
    safety: 0.35    # Familiarity and road conditions
    weather: 0.30   # Wind impact on cycling efficiency
  weather_enabled: true  # Enable real-time weather analysis
```

**Weather Analysis**: The system fetches real-time wind data and calculates the impact on each route. Headwinds slow you down, tailwinds speed you up, and crosswinds affect stability. See [WEATHER_GUIDE.md](WEATHER_GUIDE.md) for details.

### Location Detection

Fine-tune location clustering:

```yaml
location_detection:
  clustering:
    eps: 0.002           # Cluster radius (~200 meters)
    min_samples: 5       # Minimum activities to form a cluster
  time_windows:
    morning_start: "06:00"
    morning_end: "10:00"
    evening_start: "16:00"
    evening_end: "20:00"
```

### Route Filtering

Control which activities are analyzed:

```yaml
route_filtering:
  min_distance_km: 2    # Minimum commute distance
  max_distance_km: 30   # Maximum commute distance
  activity_types:
    - Ride
    - EBikeRide
  exclude_virtual: true
```

## Understanding the Report

### Executive Summary
- **Recommended Route**: The optimal route based on your criteria
- **Key Statistics**: Quick comparison of time and distance savings

### Route Comparison Table
- Lists all identified route variants
- Shows metrics: distance, duration, speed, elevation, frequency
- Displays composite scores for easy comparison

### Interactive Map
- **Red Route**: Optimal recommended route
- **Colored Routes**: Alternative route variants
- **Green Marker**: Home location
- **Blue Marker**: Work location
- **Heatmap**: Shows most frequently used paths
- Click routes for detailed statistics

### Detailed Analytics
- Time-of-day patterns
- Speed consistency analysis
- Elevation profiles
- Usage frequency trends

### Recommendations
- Primary route suggestion with rationale
- Alternative routes for variety
- Weather and traffic considerations

## Troubleshooting

### "Insufficient activities" Error

**Problem**: Not enough commute activities found.

**Solutions**:
- Ensure you have at least 10 cycling activities between two regular locations
- Check that activities have GPS data (not indoor/virtual rides)
- Adjust `min_distance_km` and `max_distance_km` in config if your commute is very short or long

### "Could not identify home/work locations" Error

**Problem**: Location clustering failed.

**Solutions**:
- Ensure your activities have consistent start/end points
- Reduce `min_samples` in config (try 3 instead of 5)
- Increase `eps` value if your start/end points vary more than 200m

### "Rate limit exceeded" Warning

**Problem**: Too many API requests to Strava.

**Solutions**:
- The app will automatically use cached data
- Wait 15 minutes before fetching new activities
- Enable caching in config (should be on by default)

### Authentication Issues

**Problem**: OAuth flow fails or tokens expire.

**Solutions**:
- Delete `config/credentials.json` and re-authenticate
- Verify your Client ID and Secret in `.env`
- Check that callback domain is set to `localhost` in Strava API settings

### "STRAVA API CREDENTIALS REQUIRED" Error

**Problem**: Application exits immediately with credential error.

**Solutions**:
- Ensure you have created a `.env` file in the project root
- Verify your credentials are correctly formatted in `.env`
- Obtain valid credentials from https://www.strava.com/settings/api
- Do not use placeholder values - you must use your actual Strava API credentials

## Project Structure

```
commute/
├── src/                      # Source code
│   ├── auth.py              # Strava authentication
│   ├── data_fetcher.py      # Activity data retrieval
│   ├── location_finder.py   # Home/work identification
│   ├── route_analyzer.py    # Route analysis
│   ├── optimizer.py         # Route optimization
│   ├── visualizer.py        # Map generation
│   └── report_generator.py  # HTML report creation
├── config/
│   ├── config.yaml          # User configuration
│   └── credentials.json     # API tokens (auto-generated)
├── data/
│   └── cache/               # Cached activity data
├── output/
│   └── reports/             # Generated reports
├── tests/                   # Unit tests
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── main.py                  # Entry point
└── README.md               # This file
```

## Data Privacy & Security

- All data is stored locally on your computer
- API credentials are stored in `.env` and `config/credentials.json`
- No data is sent to any third-party services
- The application validates Strava API credentials at startup to prevent unauthorized use
- Add `.env` and `config/credentials.json` to `.gitignore` if using version control

**Security Features:**
- Mandatory credential validation before any operations
- Application exits immediately if credentials are missing or invalid
- Protects against unauthorized redistribution and use

## Advanced Features

### Custom Scoring

Create your own scoring function by modifying `src/optimizer.py`:

```python
def calculate_custom_score(self, route_group: RouteGroup) -> float:
    # Your custom logic here
    return score
```

### Export Data

Access raw data for further analysis:

```python
from src.data_fetcher import StravaDataFetcher

fetcher = StravaDataFetcher(client)
activities = fetcher.load_cached_activities()

# Export to CSV
import pandas as pd
df = pd.DataFrame([vars(a) for a in activities])
df.to_csv('my_activities.csv')
```

### Batch Analysis

Analyze multiple time periods:

```bash
# Analyze last 3 months
python main.py --analyze --months 3

# Analyze specific date range
python main.py --analyze --start 2024-01-01 --end 2024-03-31
```

## Algorithm Improvements

### Route Matching (March 2026)

The system uses an advanced **Fréchet distance** algorithm for route similarity matching:

**Key Features:**
- **Path-aware matching**: Considers the order of GPS points (like walking a dog on a leash)
- **Robust to GPS sampling**: Handles ~76m average spacing between GPS points
- **Dual validation**: Uses Hausdorff distance as secondary check for spatial proximity
- **Proven accuracy**: Validated on 9,251 route pairs with 100% agreement

**Technical Details:**
- Primary metric: Fréchet distance (300m threshold)
- Secondary validation: Hausdorff distance (0.50 threshold)
- Grouping threshold: 0.70 similarity score (configurable)
- Library: `similaritymeasures` package

See [SIMILARITY_ALGORITHM_CHANGE.md](SIMILARITY_ALGORITHM_CHANGE.md) for complete technical documentation.

## Contributing

Contributions are welcome! Areas for improvement:

- Weather data integration
- Traffic pattern analysis
- Mobile app version
- Additional visualization options
- Machine learning for route prediction

## FAQ

**Q: How many activities do I need?**
A: Minimum 10 commute activities, but 20+ is recommended for better analysis.

**Q: Can I analyze routes other than commutes?**
A: Yes! Modify the location detection to identify any two frequent locations.

**Q: Does this work with running activities?**
A: The code is optimized for cycling, but can be adapted for running by changing activity types in config.

**Q: How often should I re-run the analysis?**
A: Run monthly or after accumulating 10+ new commute activities.

**Q: Can I compare different time periods?**
A: Yes, use the `--start` and `--end` flags to analyze specific date ranges.

## Version History

### v2.4.0 (2026-03-30)
**Long Rides Feature & Polish**

- 🚵 **NEW: Long Rides Analysis** - Comprehensive analysis of non-commute rides
  - Statistics dashboard with total rides, average distance, longest ride, elevation gain
  - Top 10 longest rides table with Strava links
  - Monthly breakdown chart showing ride count and distance trends
  - Interactive map visualizing all long rides (>15km) with color-coded routes
  - Route filtering (loops vs. point-to-point)
  - Detailed metrics for each ride (speed, elevation, duration, route type)
- 📱 **Mobile Optimizations** - Enhanced mobile performance
  - Lazy loading for maps and charts
  - Canvas renderer for mobile maps
  - Coordinate simplification on mobile devices
  - Reduced animations and hover effects on touch devices
- ✅ **Form Validation** - Real-time validation with visual feedback
  - Bootstrap validation classes with colored borders
  - Range validation for distance and time inputs
  - Invalid/valid feedback messages
- 🎨 **Animation Performance** - GPU-accelerated animations
  - Smooth fade-in, slide-in, and scale-in animations
  - Automatic cleanup of will-change hints
  - Reduced motion support for accessibility
  - Performance monitoring and adaptive animations
- 📚 **Documentation** - Enhanced setup instructions for new users
  - Detailed Python installation verification
  - Step-by-step virtual environment setup
  - Troubleshooting for common installation issues
  - Platform-specific instructions (macOS/Linux/Windows)

### v2.3.0 (2026-03-27)
**Segment-Based Route Naming & Security Enhancements**

- ✨ **NEW: Intelligent Route Naming** - Routes now show complete journey context
  - Segment-based naming: "Start St → Main St → End St"
  - Increased sampling density from 5 to 10 points
  - Automatic segment identification and classification
  - Configurable via `route_naming` section in config.yaml
- 🔒 **Security: SHA256 Migration** - Replaced MD5 with SHA256 for all cache keys
- 🛡️ **Code Quality: Exception Handling** - All bare `except:` statements replaced with specific exception types
- 📚 **Documentation: Technical Spec Updates** - Comprehensive updates to reflect new implementations
- ✅ **Testing: 100% Pass Rate** - All 43 tests passing

### v2.2.0 (2026-03-27)
**Test Infrastructure & Cache Separation**

- ✅ Test suite remediation (43/43 tests passing)
- 🔧 Separated test and production cache files
- 📝 Comprehensive test documentation

### v2.1.0 (2026-03-26)
**Performance & Route Naming Improvements**

- ⚡ Code cleanup and performance optimization
- 🏷️ Improved route naming mechanism
- 🗺️ Optimal route map preview at top of page
- 💾 Fréchet distance caching

## License

MIT License - feel free to use and modify as needed.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the technical specification in `TECHNICAL_SPEC.md`
3. Check Strava API documentation: https://developers.strava.com/

## Acknowledgments

- Built with [stravalib](https://github.com/stravalib/stravalib)
- Maps powered by [Folium](https://python-visualization.github.io/folium/)
- Inspired by the cycling community's love for data and optimization

---

**Happy Commuting! 🚴‍♂️**