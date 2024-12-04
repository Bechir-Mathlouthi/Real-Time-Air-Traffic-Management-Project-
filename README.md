# Air Traffic Management System

A lightweight Python-based web application for monitoring and analyzing air traffic data with basic AI capabilities. The system fetches real-time flight data, provides predictions for delays, and displays the information on an interactive dashboard.

## Features

- Real-time flight tracking using OpenSky Network API
- Interactive map visualization with flight markers
- AI-powered delay predictions
- Flight statistics and analytics
- Automatic data refresh
- SQLite database for historical data storage

## Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ATM
```

2. Create and activate a virtual environment:
```bash
python -m venv ATM_env
source ATM_env/bin/activate  # On Unix/macOS
.\ATM_env\Scripts\Activate.ps1  # On Windows PowerShell
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. (Optional) Set up OpenSky Network credentials:
   - Create a free account at [OpenSky Network](https://opensky-network.org/)
   - Set environment variables:
     ```bash
     export OPENSKY_USERNAME="your_username"
     export OPENSKY_PASSWORD="your_password"
     ```
     Or create a `.env` file with these credentials.

2. The application uses default settings in `src/config.py`. Modify them as needed:
   - MAP_CENTER: Default map center coordinates
   - REGION_BOUNDS: Geographic region for flight tracking
   - REFRESH_INTERVAL: Data update frequency

## Usage

1. Run the Streamlit application:
```bash
streamlit run src/app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. The dashboard will automatically:
   - Fetch real-time flight data
   - Display flights on the interactive map
   - Show flight statistics and analytics
   - Update periodically (if auto-refresh is enabled)

## Project Structure

```
ATM/
├── src/
│   ├── app.py              # Main Streamlit application
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database operations
│   ├── opensky_client.py   # OpenSky API client
│   └── predictor.py        # AI prediction module
├── data/                   # Database and data files
├── models/                 # Trained ML models
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Technical Details

- **Frontend**: Streamlit dashboard with Folium maps and Plotly charts
- **Backend**: Python with SQLite database
- **Data Source**: OpenSky Network API
- **AI Model**: Random Forest Classifier for delay predictions
- **Data Storage**: SQLite database for historical data

## Limitations

- The delay prediction model uses synthetic training data
- OpenSky Network API has rate limits for anonymous users
- Geographic coverage depends on OpenSky Network data availability

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 