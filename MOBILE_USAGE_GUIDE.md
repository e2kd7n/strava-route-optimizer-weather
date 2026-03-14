# 📱 Mobile Usage Guide

## Using Your Commute Report on Your Phone

Your Strava Commute Analysis report is now mobile-friendly! You can view it on your phone and it will automatically fetch updated weather data when you have an internet connection.

## 🚀 Quick Start

### Step 1: Generate the Report
On your computer, run:
```bash
python3 main.py --analyze
```

This creates `commute_report.html` in your project directory.

### Step 2: Transfer to Your Phone

#### Option A: AirDrop (iPhone/Mac)
1. Right-click `commute_report.html` on your Mac
2. Select "Share" → "AirDrop"
3. Send to your iPhone
4. Save to Files app (iCloud Drive or "On My iPhone")

#### Option B: Email
1. Email `commute_report.html` to yourself
2. Open email on your phone
3. Download the attachment
4. Save to Files app (iPhone) or Downloads (Android)

#### Option C: Cloud Storage
1. Upload `commute_report.html` to iCloud Drive, Google Drive, or Dropbox
2. Open the file from the cloud storage app on your phone

#### Option D: USB Cable (Android)
1. Connect phone to computer via USB
2. Copy `commute_report.html` to your phone's storage
3. Use a file manager app to locate it

### Step 3: Open on Your Phone

#### iPhone:
1. Open Files app
2. Navigate to where you saved the file
3. Tap `commute_report.html`
4. It will open in Safari

#### Android:
1. Open your file manager app
2. Navigate to Downloads or where you saved it
3. Tap `commute_report.html`
4. Choose a browser (Chrome, Firefox, etc.)

## ✨ Features That Work on Mobile

### ✅ Works Perfectly:
- **All route analysis and recommendations** - Static data embedded in the file
- **Interactive maps** - Powered by Leaflet.js (requires internet)
- **Charts and visualizations** - Powered by Chart.js (requires internet)
- **Route comparison tables** - All data is embedded
- **Long ride recommendations** - Weather updates require internet
- **Responsive design** - Optimized for mobile screens

### 🌐 Requires Internet Connection:
- **Weather updates** - Fetches current conditions from weather API
- **Map tiles** - Downloads map imagery from OpenStreetMap
- **CDN resources** - Bootstrap, Chart.js, and Leaflet libraries

### ❌ Not Available on Mobile:
- **Refresh button** - Requires running Python on your computer
- **Generating new reports** - Must be done on your computer

## 🔄 Updating Your Report

To get fresh data with your latest Strava activities:

1. **On your computer**, run:
   ```bash
   python3 main.py --analyze
   ```

2. **Transfer the new file** to your phone using any method above

3. **Replace the old file** or save with a new name (e.g., `commute_report_2026-03-14.html`)

## 💡 Pro Tips

### Bookmark It
- Add the report to your home screen for quick access
- **iPhone**: Open in Safari → Share → "Add to Home Screen"
- **Android**: Open in Chrome → Menu → "Add to Home Screen"

### Offline Viewing
- The report data is embedded, so route analysis works offline
- Maps and weather require internet, but you can still see your routes and scores

### Multiple Reports
- Save reports with dates in the filename: `commute_report_2026-03-14.html`
- Compare your progress over time

### Battery Saving
- The report is just HTML - very lightweight
- No background processes or battery drain
- Close the browser tab when done

## 🔒 Privacy & Security

- **All your data stays local** - The HTML file contains your data
- **No tracking** - No analytics or third-party tracking scripts
- **Secure** - Anti-piracy protection prevents unauthorized hosting
- **Your data only** - File only works when opened locally (file://) or on localhost

## 🐛 Troubleshooting

### Maps Not Loading
- **Check internet connection** - Maps require downloading tiles
- **Try a different browser** - Some browsers block mixed content
- **Wait a moment** - Map tiles can take a few seconds to load

### Weather Not Updating
- **Requires internet** - Weather data is fetched from API
- **Check API limits** - Free tier has request limits
- **Try refreshing** - Close and reopen the file

### File Won't Open
- **Use a browser** - Don't try to open in a text editor
- **Check file extension** - Must be `.html`
- **Try different browser** - Safari (iPhone) or Chrome (Android)

### Blank Page or Errors
- **Check internet connection** - CDN resources need to download
- **Clear browser cache** - Old cached resources might conflict
- **Re-transfer file** - File might have been corrupted during transfer

## 📊 What You Can Do on Mobile

### View Your Routes
- See all your commute route variants
- Compare performance metrics
- View route maps and polylines

### Check Weather Impact
- See how wind affects each route
- View current weather conditions
- Get real-time route recommendations

### Plan Long Rides
- Enter start location and ride date/time
- Get wind-optimized route recommendations
- See detailed wind analysis for each segment

### Analyze Performance
- View your riding statistics
- See route frequency and consistency
- Compare different route options

## 🎯 Best Practices

1. **Update Weekly** - Generate a fresh report once a week
2. **Keep Old Reports** - Save with dates to track progress
3. **Check Before Commute** - View weather-optimized recommendations
4. **Use Offline** - Route data works without internet
5. **Share Carefully** - File contains your personal riding data

## 🆘 Need Help?

If you encounter issues:
1. Check this guide first
2. Verify internet connection for weather/maps
3. Try a different browser
4. Re-generate and re-transfer the file
5. Check the main README.md for general troubleshooting

---

**Enjoy your mobile commute analysis! 🚴📱**