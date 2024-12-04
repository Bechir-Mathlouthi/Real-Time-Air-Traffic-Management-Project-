import streamlit as st
import folium
from streamlit_folium import folium_static
import plotly.express as px
import pandas as pd
from datetime import datetime
import time
import numpy as np

from opensky_client import OpenSkyClient
from predictor import DelayPredictor
from database import init_db, store_flight_data, get_recent_flights, store_prediction
from config import MAP_CENTER, MAP_ZOOM, REFRESH_INTERVAL

def create_map(flights_df):
    """Create a folium map with flight markers."""
    # Debug information
    st.write(f"Number of flights to display: {len(flights_df)}")
    
    # Create the map centered on the specified location
    m = folium.Map(location=MAP_CENTER, zoom_start=MAP_ZOOM)
    
    # Add markers for each flight
    for _, flight in flights_df.iterrows():
        try:
            # Create popup content
            popup_content = f"""
                <b>Flight Info:</b><br>
                Callsign: {flight['callsign']}<br>
                Country: {flight['origin_country']}<br>
                Altitude: {flight['altitude']:.0f}m<br>
                Velocity: {flight['velocity']:.0f}m/s<br>
                Delay Prob: {flight.get('delay_probability', 0):.1%}
            """
            
            # Add marker to map
            folium.CircleMarker(
                location=[float(flight['latitude']), float(flight['longitude'])],
                radius=6,
                popup=popup_content,
                color='red' if flight.get('delay_probability', 0) > 0.5 else 'blue',
                fill=True
            ).add_to(m)
        except Exception as e:
            st.error(f"Error adding marker for flight {flight.get('callsign')}: {str(e)}")
            continue
    
    return m

def main():
    # Set page config
    st.set_page_config(
        page_title="Air Traffic Management System",
        page_icon="✈️",
        layout="wide"
    )
    
    # Title and description
    st.title("✈️ Air Traffic Management System")
    st.markdown("Real-time flight tracking and delay prediction system")
    
    # Initialize components
    opensky_client = OpenSkyClient()
    delay_predictor = DelayPredictor()
    init_db()
    
    # Sidebar
    st.sidebar.title("Controls")
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Live Flight Map")
        
        # Add a refresh button
        if st.button("🔄 Refresh Data") or auto_refresh:
            with st.spinner("Fetching flight data..."):
                # Fetch and process flight data
                flights = opensky_client.get_states()
                
                if flights:
                    try:
                        # Create DataFrame
                        df = pd.DataFrame(flights)
                        st.write(f"Raw data shape: {df.shape}")
                        
                        # Get delay predictions
                        df['delay_probability'] = df.apply(
                            lambda x: delay_predictor.predict_delay(x),
                            axis=1
                        )
                        
                        # Store data
                        store_flight_data(flights)
                        
                        # Create and display map
                        st.write("Creating map...")
                        m = create_map(df)
                        folium_static(m, width=800)
                        
                        # Display statistics
                        with col2:
                            st.subheader("Flight Statistics")
                            
                            # Basic stats
                            st.metric("Total Flights", len(df))
                            if len(df) > 0:
                                st.metric("Average Altitude", f"{df['altitude'].mean():.0f}m")
                                st.metric("Average Velocity", f"{df['velocity'].mean():.0f}m/s")
                                
                                # Delay probability histogram
                                st.subheader("Delay Probability Distribution")
                                fig = px.histogram(
                                    df,
                                    x='delay_probability',
                                    nbins=20,
                                    labels={'delay_probability': 'Delay Probability'},
                                    title='Distribution of Delay Probabilities'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Top countries
                                st.subheader("Top 10 Countries")
                                country_counts = df['origin_country'].value_counts().head(10)
                                fig = px.bar(
                                    x=country_counts.index,
                                    y=country_counts.values,
                                    labels={'x': 'Country', 'y': 'Number of Flights'},
                                    title='Flights by Country'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                    
                    except Exception as e:
                        st.error(f"Error processing flight data: {str(e)}")
                else:
                    st.error("No flight data available. Please check your connection and API credentials.")
        
        # Show data refresh time
        st.text(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Auto refresh
    if auto_refresh:
        time.sleep(REFRESH_INTERVAL)
        st.experimental_rerun()

if __name__ == "__main__":
    main() 