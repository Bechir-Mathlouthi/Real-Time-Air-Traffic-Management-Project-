import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime
import os
from config import MODEL_PATH

class DelayPredictor:
    def __init__(self):
        """Initialize the delay predictor."""
        self.model = None
        self.scaler = None
        self.feature_columns = ['velocity', 'altitude', 'distance_to_dest', 'hour_of_day']
        self.model_path = MODEL_PATH
        self.scaler_path = str(MODEL_PATH).replace('.pkl', '_scaler.pkl')
        self.load_or_train_model()
    
    def load_or_train_model(self):
        """Load existing model or train a new one if none exists."""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                print("Loading existing model and scaler...")
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
            else:
                print("No existing model found. Training new model...")
                self._train_initial_model()
                self._save_model()
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Training new model...")
            self._train_initial_model()
            self._save_model()
    
    def _save_model(self):
        """Save the trained model and scaler."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Save model and scaler
            print(f"Saving model to {self.model_path}")
            joblib.dump(self.model, self.model_path)
            
            print(f"Saving scaler to {self.scaler_path}")
            joblib.dump(self.scaler, self.scaler_path)
            print("Model and scaler saved successfully.")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def _train_initial_model(self):
        """Train an initial model with synthetic data."""
        print("Training new model with synthetic data...")
        
        try:
            # Generate synthetic training data
            np.random.seed(42)
            n_samples = 1000
            
            # Generate synthetic features
            X = pd.DataFrame({
                'velocity': np.random.normal(250, 50, n_samples),
                'altitude': np.random.normal(10000, 2000, n_samples),
                'distance_to_dest': np.random.uniform(0, 1000, n_samples),
                'hour_of_day': np.random.randint(0, 24, n_samples)
            })
            
            # Ensure all feature columns are present
            for col in self.feature_columns:
                if col not in X.columns:
                    X[col] = 0.0
            
            # Generate synthetic labels (0: no delay, 1: delay)
            y = ((X['velocity'] < 200) | (X['altitude'] < 8000)).astype(int)
            
            # Initialize and fit scaler
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X[self.feature_columns])
            
            # Train model
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_scaled, y)
            
            print("Model training completed successfully.")
        except Exception as e:
            print(f"Error training model: {e}")
            raise
    
    def predict_delay(self, flight_data):
        """Predict delay probability for a flight."""
        try:
            if self.model is None or self.scaler is None:
                print("Model or scaler not initialized. Retraining...")
                self._train_initial_model()
                self._save_model()
            
            # Create a DataFrame with all required features
            features = pd.DataFrame({
                'velocity': [float(flight_data.get('velocity', 0))],
                'altitude': [float(flight_data.get('altitude', 0))],
                'distance_to_dest': [0.0],  # Placeholder
                'hour_of_day': [float(datetime.fromtimestamp(flight_data.get('timestamp', 0)).hour)]
            })
            
            # Ensure all feature columns are present and in correct order
            for col in self.feature_columns:
                if col not in features.columns:
                    features[col] = 0.0
            
            # Scale features using only the specified columns in the correct order
            X_scaled = self.scaler.transform(features[self.feature_columns])
            
            # Get prediction probability
            delay_prob = self.model.predict_proba(X_scaled)[0][1]
            
            return float(delay_prob)
            
        except Exception as e:
            print(f"Error in prediction: {e}")
            print("Flight data:", flight_data)
            return 0.0