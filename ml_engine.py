import numpy as np
from sklearn.linear_model import LinearRegression
import logging
import joblib
import os

logger = logging.getLogger("TeknoNexus-ML")

class InnovationPredictor:
    """Model ML untuk memprediksi potensi pertumbuhan berdasarkan maturitas teknologi."""
    def __init__(self):
        self.model_path = 'data/innovation_model.pkl'
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print(f"[ML] Loaded existing model from {self.model_path}")
                return
            except Exception as e:
                logger.error(f"Error loading model: {e}. Retraining...")
        
        self.model = LinearRegression()
        self._train_model()

    def _train_model(self):
        # Data Pelatihan (Simulasi: [Maturitas Teknologi, Log GDP Current])
        X_train = np.array([
            [98, 13], [95, 12.5], [94, 12.3], [96, 12.7], [75, 12], 
            [85, 11.5], [60, 10], [90, 11.8], [70, 10.5]
        ])
        y_train = np.array([3.2, 2.8, 2.5, 3.0, 5.2, 4.8, 6.5, 3.5, 5.5])
        self.model.fit(X_train, y_train)
        
        # Simpan model untuk penggunaan berikutnya
        try:
            joblib.dump(self.model, self.model_path)
            print(f"[ML] Model trained and saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def predict_growth(self, tech_maturity, current_gdp):
        try:
            # Validasi input
            if not isinstance(current_gdp, (int, float)) or current_gdp <= 0:
                logger.warning(f"Invalid GDP input for prediction: {current_gdp}")
                return 0.0
                
            log_gdp = np.log10(current_gdp)
            prediction = self.model.predict([[tech_maturity, log_gdp]])
            return round(float(prediction[0]), 2)
        except Exception as e:
            logger.error(f"ML Prediction Error: {e}")
            return 0.0
