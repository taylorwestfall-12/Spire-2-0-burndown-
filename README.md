# Spire 2.0.0 Bug Burndown Dashboard

Interactive bug burndown projection dashboard for the Spire 2.0.0 Global release.

## 📊 Live Dashboard

**🔗 https://taylorwestfall-12.github.io/Spire-2-0-burndown-/**

View the interactive dashboard with real-time bug projections, weekend plateaus, and milestone tracking.

## 🎯 What It Shows

- **Ideal Line** (Black): Required burn rate to hit zero bugs by Code Freeze (June 2, 2026)
- **Estimated Line** (Orange): Projected trajectory based on historical or recent performance
- **Actual Line** (Green): Real daily bug counts from ClickUp

### Key Features

- Weekend plateaus (no progress on Sat/Sun)
- Auto-switching rate calculation (historical → last 10 business days)
- Milestone markers for Code Freeze, Submit, and Go Live
- Real-time metrics: Active bugs, required rate, velocity gap

## 🔧 How It Works

1. **Data Collection**: Fetches bug data from ClickUp
2. **Rate Calculation**: Analyzes historical performance (6-month window)
3. **Projection**: Generates three projection lines with weekend awareness
4. **Dashboard**: Creates interactive Plotly chart with Twilight Towers branding

## 📁 Files

- `calculate_burndown_projections.py` - Generates projection data
- `generate_burndown_projection_chart.py` - Creates HTML dashboard
- `calculate_historical_actuals.py` - Retroactive daily counts (May 11-21)
- `calculate_historical_rate.py` - Historical burndown rate from past releases
- `docs/index.html` - GitHub Pages dashboard (auto-published)

## 🚀 Usage

### Generate Dashboard Locally

```bash
# Calculate projections
python calculate_burndown_projections.py

# Generate dashboard
python generate_burndown_projection_chart.py

# Open spire_2_0_projection_dashboard.html in browser
```

### Update Data

```bash
# Future: Automated daily updates via update_actual_burndown.py
python update_actual_burndown.py
```

## 📅 Milestone Dates

- **Code Freeze**: June 2, 2026
- **Submit**: June 10, 2026
- **Go Live**: June 15, 2026

## 🏢 Twilight Towers Branding

Dashboard features custom Twilight Towers visual identity:
- Purple gradient background (#3B2A5C → #2A1F42)
- Gold accents (#F4C542)
- Logo integration

---

*Generated with Claude Code*
