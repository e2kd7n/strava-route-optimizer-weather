# Strava Commute Route Analyzer

A Python application that analyzes your Strava cycling activities to determine the optimal commute route between home and work, considering time, distance, and safety factors.

## Features

- 🔍 **Automatic Location Detection**: Identifies your home and work locations from activity patterns
- 📊 **Multi-Criteria Analysis**: Evaluates routes based on time, distance, safety, and weather
- 🧮 **Advanced Route Matching**: Uses Fréchet distance algorithm for accurate path similarity detection
- 🌤️ **Real-Time Weather Analysis**: Considers wind speed and direction for optimal route selection
- 🗺️ **Interactive Maps**: Generates beautiful HTML reports with interactive route visualizations
- 📈 **Detailed Statistics**: Provides comprehensive metrics for each route variant
- ⚡ **Smart Caching**: Minimizes API calls by caching activity data locally
- 🎯 **Personalized Recommendations**: Suggests optimal routes based on your preferences and current conditions

## How It Works

1. **Fetches Your Activities**: Retrieves your cycling activities from Strava
2. **Identifies Locations**: Uses clustering algorithms to find your home and work locations
3. **Analyzes Routes**: Groups similar routes and calculates detailed metrics
4. **Optimizes Selection**: Scores routes based on time, distance, and safety factors
5. **Generates Report**: Creates an interactive HTML report with maps and recommendations

## Prerequisites

- Python 3.8 or higher
- A Strava account with cycling activities
- Strava API credentials (free to obtain)

## Installation

### 1. Clone or Download

```bash
cd ~/commute
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Strava API Credentials

1. Go to https://www.strava.com/settings/api
2. Create a new application:
   - **Application Name**: Commute Analyzer (or any name)
   - **Category**: Data Importer
   - **Website**: http://localhost
   - **Authorization Callback Domain**: localhost
3. Note your **Client ID** and **Client Secret**

### 5. Configure Environment

Create a `.env` file in the project root:

```bash
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
```

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

### Basic Commands

```bash
# Authenticate with Strava (first time only)
python main.py --auth

# Fetch new activities and update cache
python main.py --fetch

# Run full analysis and generate report
python main.py --analyze

# Fetch and analyze in one command
python main.py --fetch --analyze
```

### Advanced Options

```bash
# Use custom configuration file
python main.py --analyze --config my_config.yaml

# Specify output directory
python main.py --analyze --output ~/Desktop/reports

# Combine options
python main.py --fetch --analyze --output ./my_reports
```

## Configuration

Edit `config/config.yaml` to customize the analysis:

### Optimization Weights

Adjust how routes are scored:

```yaml
optimization:
  weights:
    time: 0.35      # 35% weight on speed
    distance: 0.25  # 25% weight on distance
    safety: 0.25    # 25% weight on safety
    weather: 0.15   # 15% weight on wind conditions
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

## Data Privacy

- All data is stored locally on your computer
- API credentials are stored in `.env` and `config/credentials.json`
- No data is sent to any third-party services
- Add `.env` and `config/credentials.json` to `.gitignore` if using version control

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