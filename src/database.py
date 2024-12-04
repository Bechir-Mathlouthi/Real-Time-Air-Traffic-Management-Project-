import sqlite3
from datetime import datetime
import pandas as pd
from config import DATABASE_PATH

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create flights table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icao24 TEXT,
            callsign TEXT,
            origin_country TEXT,
            longitude REAL,
            latitude REAL,
            altitude REAL,
            velocity REAL,
            heading REAL,
            timestamp INTEGER,
            on_ground BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create predictions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icao24 TEXT,
            delay_probability REAL,
            predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def store_flight_data(flight_data):
    """Store flight data in the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    df = pd.DataFrame(flight_data)
    df.to_sql('flights', conn, if_exists='append', index=False)
    conn.close()
    return True

def get_recent_flights(limit=100):
    """Retrieve recent flights from the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    query = '''
        SELECT * FROM flights 
        ORDER BY timestamp DESC 
        LIMIT ?
    '''
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()
    return df

def store_prediction(flight_data, delay_probability):
    """Store delay prediction for a flight."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO predictions (icao24, delay_probability)
        VALUES (?, ?)
    ''', (flight_data.get('icao24'), delay_probability))
    conn.commit()
    conn.close()
    return True 