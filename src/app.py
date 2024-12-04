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

# Custom CSS for better styling
def local_css():
    st.markdown("""
    <style>
        .main-header {
            background-color: #1E1E1E;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .main-header h1 {
            color: white !important;
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            margin-bottom: 0.5rem !important;
        }
        .main-header p {
            color: #f0f0f0 !important;
            font-size: 1.2rem !important;
            margin-top: 0.5rem !important;
        }
        .main-header a {
            color: #FF4B4B !important;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.3s ease;
        }
        .main-header a:hover {
            color: #ff7676 !important;
            text-decoration: underline;
        }
        .stat-box {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            text-align: center;
        }
        .chart-container {
            background-color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .footer {
            background-color: #1E1E1E;
            padding: 1rem;
            border-radius: 10px;
            margin-top: 2rem;
            text-align: center;
            color: white;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            background-color: #FF4B4B;
            color: white;
        }
        .sidebar-content {
            padding: 1.5rem;
            background-color: #f0f2f6;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

def create_map(flights_df):
    """Create a folium map with flight markers."""
    # Create the map centered on the specified location
    m = folium.Map(location=MAP_CENTER, zoom_start=MAP_ZOOM, control_scale=True)
    
    # Add markers for each flight
    for _, flight in flights_df.iterrows():
        try:
            # Create popup content with improved styling
            popup_content = f"""
                <div style='font-family: Arial, sans-serif; padding: 10px;'>
                    <h4 style='margin-bottom: 10px; color: #1E1E1E;'>Flight Information</h4>
                    <table style='width: 100%;'>
                        <tr><td><b>Callsign:</b></td><td>{flight['callsign']}</td></tr>
                        <tr><td><b>Country:</b></td><td>{flight['origin_country']}</td></tr>
                        <tr><td><b>Altitude:</b></td><td>{flight['altitude']:.0f}m</td></tr>
                        <tr><td><b>Velocity:</b></td><td>{flight['velocity']:.0f}m/s</td></tr>
                        <tr><td><b>Delay Prob:</b></td><td>{flight.get('delay_probability', 0):.1%}</td></tr>
                    </table>
                </div>
            """
            
            # Add marker to map with custom icon
            folium.CircleMarker(
                location=[float(flight['latitude']), float(flight['longitude'])],
                radius=6,
                popup=folium.Popup(popup_content, max_width=300),
                color='red' if flight.get('delay_probability', 0) > 0.5 else 'blue',
                fill=True,
                fill_opacity=0.7,
                weight=2
            ).add_to(m)
        except Exception as e:
            st.error(f"Error adding marker for flight {flight.get('callsign')}: {str(e)}")
            continue
    
    return m

def display_metrics(df):
    """Display key metrics in a grid layout."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class='stat-box'>
            <h3>Total Flights</h3>
            <h2>{}</h2>
        </div>
        """.format(len(df)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='stat-box'>
            <h3>Average Altitude</h3>
            <h2>{:.0f}m</h2>
        </div>
        """.format(df['altitude'].mean()), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='stat-box'>
            <h3>Average Velocity</h3>
            <h2>{:.0f}m/s</h2>
        </div>
        """.format(df['velocity'].mean()), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='stat-box'>
            <h3>Countries</h3>
            <h2>{}</h2>
        </div>
        """.format(df['origin_country'].nunique()), unsafe_allow_html=True)

def filter_flights(df, min_altitude=None, min_velocity=None, country=None, delay_threshold=None):
    """Filter flights based on criteria."""
    filtered_df = df.copy()
    
    if min_altitude:
        filtered_df = filtered_df[filtered_df['altitude'] >= min_altitude]
    if min_velocity:
        filtered_df = filtered_df[filtered_df['velocity'] >= min_velocity]
    if country:
        filtered_df = filtered_df[filtered_df['origin_country'].str.contains(country, case=False, na=False)]
    if delay_threshold:
        filtered_df = filtered_df[filtered_df['delay_probability'] >= delay_threshold]
    
    return filtered_df

def calculate_statistics(df):
    """Calculate advanced statistics."""
    stats = {
        'total_flights': len(df),
        'active_countries': df['origin_country'].nunique(),
        'avg_altitude': df['altitude'].mean(),
        'avg_velocity': df['velocity'].mean(),
        'high_risk_flights': len(df[df['delay_probability'] > 0.7]),
        'low_altitude_flights': len(df[df['altitude'] < 5000]),
        'high_speed_flights': len(df[df['velocity'] > 300]),
        'busiest_country': df['origin_country'].value_counts().index[0],
        'busiest_country_flights': df['origin_country'].value_counts().iloc[0]
    }
    return stats

def create_heatmap(df):
    """Create a heatmap of flight density."""
    return px.density_mapbox(df, 
                           lat='latitude', 
                           lon='longitude', 
                           radius=10,
                           center=dict(lat=MAP_CENTER[0], lon=MAP_CENTER[1]), 
                           zoom=5,
                           mapbox_style="stamen-terrain")

def calculate_advanced_analytics(df):
    """Calculate comprehensive flight analytics."""
    stats = {
        'operational_metrics': {
            'total_flights': len(df),
            'active_countries': df['origin_country'].nunique(),
            'avg_altitude': df['altitude'].mean(),
            'avg_velocity': df['velocity'].mean(),
        },
        'risk_analysis': {
            'high_risk_flights': len(df[df['delay_probability'] > 0.7]),
            'medium_risk_flights': len(df[(df['delay_probability'] > 0.4) & (df['delay_probability'] <= 0.7)]),
            'low_risk_flights': len(df[df['delay_probability'] <= 0.4]),
            'risk_index': (df['delay_probability'] * df['velocity']).mean(),
        },
        'altitude_analysis': {
            'low_altitude': len(df[df['altitude'] < 5000]),
            'medium_altitude': len(df[(df['altitude'] >= 5000) & (df['altitude'] < 10000)]),
            'high_altitude': len(df[df['altitude'] >= 10000]),
            'avg_altitude_by_country': df.groupby('origin_country')['altitude'].mean().to_dict()
        },
        'velocity_analysis': {
            'slow_flights': len(df[df['velocity'] < 200]),
            'medium_speed': len(df[(df['velocity'] >= 200) & (df['velocity'] < 400)]),
            'high_speed': len(df[df['velocity'] >= 400]),
            'avg_velocity_by_country': df.groupby('origin_country')['velocity'].mean().to_dict()
        },
        'geographical_distribution': {
            'country_distribution': df['origin_country'].value_counts().to_dict(),
            'latitude_range': [df['latitude'].min(), df['latitude'].max()],
            'longitude_range': [df['longitude'].min(), df['longitude'].max()]
        }
    }
    return stats

def create_advanced_visualizations(df):
    """Create advanced visualizations for analytics."""
    visualizations = {}
    
    # Flight Distribution Map
    visualizations['density_map'] = px.density_mapbox(
        df,
        lat='latitude',
        lon='longitude',
        z='delay_probability',
        radius=20,
        center=dict(lat=MAP_CENTER[0], lon=MAP_CENTER[1]),
        zoom=4,
        mapbox_style="stamen-terrain",
        title="Flight Risk Distribution Heatmap",
        color_continuous_scale="Viridis"
    )
    
    # Altitude vs Velocity Scatter
    visualizations['altitude_velocity'] = px.scatter(
        df,
        x='velocity',
        y='altitude',
        color='delay_probability',
        size='delay_probability',
        hover_data=['callsign', 'origin_country'],
        title="Altitude vs Velocity Analysis",
        labels={'velocity': 'Velocity (m/s)', 'altitude': 'Altitude (m)'},
        color_continuous_scale="RdYlBu_r"
    )
    
    # Risk Distribution by Country
    country_risk = df.groupby('origin_country')['delay_probability'].mean().reset_index()
    country_risk = country_risk.sort_values('delay_probability', ascending=False).head(10)
    visualizations['country_risk'] = px.bar(
        country_risk,
        x='origin_country',
        y='delay_probability',
        title="Average Risk by Country (Top 10)",
        color='delay_probability',
        color_continuous_scale="Reds"
    )
    
    return visualizations

def display_advanced_analytics(df):
    """Display advanced analytics section."""
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    
    # Analytics Navigation
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["Risk Assessment", "Performance Metrics", "Geographical Analysis", "Custom Analysis"]
    )
    
    # Calculate statistics
    stats = calculate_advanced_analytics(df)
    visualizations = create_advanced_visualizations(df)
    
    if analysis_type == "Risk Assessment":
        st.subheader("🎯 Flight Risk Assessment")
        
        # Risk Distribution
        risk_col1, risk_col2, risk_col3 = st.columns(3)
        with risk_col1:
            st.metric("High Risk Flights", 
                     stats['risk_analysis']['high_risk_flights'],
                     delta=f"{stats['risk_analysis']['high_risk_flights']/len(df)*100:.1f}%")
        with risk_col2:
            st.metric("Medium Risk Flights", 
                     stats['risk_analysis']['medium_risk_flights'],
                     delta=f"{stats['risk_analysis']['medium_risk_flights']/len(df)*100:.1f}%")
        with risk_col3:
            st.metric("Low Risk Flights", 
                     stats['risk_analysis']['low_risk_flights'],
                     delta=f"{stats['risk_analysis']['low_risk_flights']/len(df)*100:.1f}%")
        
        # Risk Heatmap
        st.plotly_chart(visualizations['density_map'], use_container_width=True)
        
        # Country Risk Analysis
        st.plotly_chart(visualizations['country_risk'], use_container_width=True)
        
    elif analysis_type == "Performance Metrics":
        st.subheader("📊 Flight Performance Analysis")
        
        # Altitude vs Velocity Analysis
        st.plotly_chart(visualizations['altitude_velocity'], use_container_width=True)
        
        # Performance Metrics
        perf_col1, perf_col2, perf_col3 = st.columns(3)
        with perf_col1:
            st.metric("Average Altitude", 
                     f"{stats['operational_metrics']['avg_altitude']:.0f}m",
                     delta="Above Ground")
        with perf_col2:
            st.metric("Average Velocity", 
                     f"{stats['operational_metrics']['avg_velocity']:.0f}m/s",
                     delta="Cruising Speed")
        with perf_col3:
            st.metric("Total Distance Covered", 
                     f"{len(df) * stats['operational_metrics']['avg_velocity']:.0f}m",
                     delta="Combined")
        
    elif analysis_type == "Geographical Analysis":
        st.subheader("🌍 Geographical Distribution")
        
        # Create columns for metrics
        geo_col1, geo_col2 = st.columns(2)
        
        with geo_col1:
            st.metric("Active Countries", 
                     stats['operational_metrics']['active_countries'])
            
            # Top Countries Table
            st.subheader("Top Active Countries")
            top_countries = pd.DataFrame(
                list(stats['geographical_distribution']['country_distribution'].items())[:5],
                columns=['Country', 'Flights']
            )
            st.table(top_countries)
        
        with geo_col2:
            st.metric("Coverage Area", 
                     f"{abs(stats['geographical_distribution']['latitude_range'][1] - stats['geographical_distribution']['latitude_range'][0]):.1f}° x {abs(stats['geographical_distribution']['longitude_range'][1] - stats['geographical_distribution']['longitude_range'][0]):.1f}°")
            
            # Coverage Map
            st.plotly_chart(visualizations['density_map'], use_container_width=True)
            
    else:  # Custom Analysis
        st.subheader("🔍 Custom Analysis")
        
        # Parameter Selection
        params = st.multiselect(
            "Select Parameters to Analyze",
            ['altitude', 'velocity', 'delay_probability', 'origin_country'],
            default=['altitude', 'velocity']
        )
        
        if len(params) >= 2:
            # Create correlation matrix for selected parameters
            correlation = df[params].corr()
            fig_corr = px.imshow(
                correlation,
                labels=dict(color="Correlation"),
                color_continuous_scale="RdBu",
                title="Parameter Correlation Analysis"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # Create scatter matrix
            if len(params) > 2:
                fig_scatter = px.scatter_matrix(
                    df[params],
                    dimensions=params,
                    color='delay_probability',
                    title="Multi-Parameter Analysis"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Statistical Summary
            st.subheader("Statistical Summary")
            st.dataframe(df[params].describe())
            
            # Export Option
            if st.button("📥 Export Analysis"):
                analysis_data = {
                    'correlation': correlation.to_dict(),
                    'summary_stats': df[params].describe().to_dict(),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.download_button(
                    label="Download Analysis Report",
                    data=str(analysis_data),
                    file_name="flight_analysis_report.json",
                    mime="application/json"
                )
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    # Set page config
    st.set_page_config(
        page_title="Air Traffic Management System",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    local_css()
    
    # Header
    st.markdown("""
    <div class='main-header'>
        <h1>✈️ Air Traffic Management System</h1>
        <p>Developed by <a href='https://github.com/Bechir-Mathlouthi' target='_blank'>Bechir Mathlouthi</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize components
    opensky_client = OpenSkyClient()
    delay_predictor = DelayPredictor()
    init_db()
    
    # Sidebar
    with st.sidebar:
        st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
        st.title("Control Panel")
        st.markdown("---")
        
        # Region selection
        st.subheader("🌍 Region Settings")
        region = st.selectbox("Select Region", ["France", "Europe", "North America", "Custom"])
        
        if region == "Custom":
            st.number_input("Min Latitude", value=MAP_CENTER[0]-5)
            st.number_input("Max Latitude", value=MAP_CENTER[0]+5)
            st.number_input("Min Longitude", value=MAP_CENTER[1]-5)
            st.number_input("Max Longitude", value=MAP_CENTER[1]+5)
        
        # Refresh settings
        st.subheader("🔄 Refresh Settings")
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        if auto_refresh:
            refresh_interval = st.slider("Refresh Interval (seconds)", 
                                      min_value=30, 
                                      max_value=300, 
                                      value=REFRESH_INTERVAL)
        
        # View options
        st.subheader("🎯 View Options")
        view_mode = st.radio("Map View", ["Standard", "Heatmap", "Satellite"])
        
        # Filters
        st.subheader("🔍 Filters")
        min_altitude = st.slider("Minimum Altitude (m)", 0, 20000, 0)
        min_velocity = st.slider("Minimum Velocity (m/s)", 0, 500, 0)
        country_filter = st.text_input("Filter by Country")
        delay_threshold = st.slider("Minimum Delay Probability", 0.0, 1.0, 0.0)
        
        # About section
        st.markdown("---")
        st.markdown("""
        ### 👨‍💻 About
        Developed by: **Bechir Mathlouthi**  
        [GitHub Profile](https://github.com/Bechir-Mathlouthi)
        """)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Search & Analysis", "📈 Advanced Analytics"])
    
    with tab1:
        # Refresh button and last update time
        col1, col2 = st.columns([2, 1])
        with col1:
            refresh = st.button("🔄 Refresh Data")
        with col2:
            st.text(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if refresh or auto_refresh:
            with st.spinner("Fetching flight data..."):
                flights = opensky_client.get_states()
                
                if flights:
                    try:
                        # Create DataFrame
                        df = pd.DataFrame(flights)
                        
                        # Get delay predictions
                        df['delay_probability'] = df.apply(
                            lambda x: delay_predictor.predict_delay(x),
                            axis=1
                        )
                        
                        # Store data
                        store_flight_data(flights)
                        
                        # Display metrics
                        display_metrics(df)
                        
                        # Create and display map
                        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                        m = create_map(df)
                        folium_static(m, width=1200, height=600)
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Charts
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                            st.subheader("Delay Probability Distribution")
                            fig = px.histogram(
                                df,
                                x='delay_probability',
                                nbins=20,
                                labels={'delay_probability': 'Delay Probability'},
                                title='Distribution of Delay Probabilities'
                            )
                            fig.update_layout(showlegend=False)
                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                            st.subheader("Top 10 Countries")
                            country_counts = df['origin_country'].value_counts().head(10)
                            fig = px.bar(
                                x=country_counts.index,
                                y=country_counts.values,
                                labels={'x': 'Country', 'y': 'Number of Flights'},
                                title='Flights by Country'
                            )
                            fig.update_layout(showlegend=False)
                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    except Exception as e:
                        st.error(f"Error processing flight data: {str(e)}")
                else:
                    st.error("No flight data available. Please check your connection and API credentials.")
    
    with tab2:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("🔍 Flight Search and Analysis")
        
        # Search functionality
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_term = st.text_input("Search Flights (by callsign or country)")
        with search_col2:
            sort_by = st.selectbox("Sort By", ["Altitude", "Velocity", "Delay Probability"])
        
        if 'df' in locals():
            # Filter and sort data
            filtered_df = filter_flights(df, min_altitude, min_velocity, country_filter, delay_threshold)
            if search_term:
                filtered_df = filtered_df[
                    filtered_df['callsign'].str.contains(search_term, case=False, na=False) |
                    filtered_df['origin_country'].str.contains(search_term, case=False, na=False)
                ]
            
            # Display results
            st.write(f"Found {len(filtered_df)} flights matching criteria")
            
            # Display detailed flight table
            st.dataframe(
                filtered_df[[
                    'callsign', 'origin_country', 'altitude', 
                    'velocity', 'delay_probability'
                ]].sort_values(sort_by.lower(), ascending=False),
                height=400
            )
            
            # Export options
            if st.button("📥 Export Results"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="flight_data.csv",
                    mime="text/csv"
                )
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        if 'df' in locals():
            display_advanced_analytics(df)
        else:
            st.error("No flight data available for analysis. Please wait for data to load.")
    
    # Footer
    st.markdown("""
    <div class='footer'>
        <p>© 2024 Bechir Mathlouthi | <a href='https://github.com/Bechir-Mathlouthi/Real-Time-Air-Traffic-Management-Project-' target='_blank' style='color: #FF4B4B;'>Project Repository</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto refresh
    if auto_refresh:
        time.sleep(refresh_interval if 'refresh_interval' in locals() else REFRESH_INTERVAL)
        st.experimental_rerun()

if __name__ == "__main__":
    main() 