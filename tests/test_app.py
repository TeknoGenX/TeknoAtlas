import pytest
from unittest.mock import patch, MagicMock
from app import app as flask_app
import numpy as np

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "CACHE_TYPE": "NullCache"
    })
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

# ==========================================
# 1. UNIT TEST: ML ENGINE
# ==========================================
class TestMLEngine:
    def test_predict_growth_valid(self):
        from ml_engine import InnovationPredictor
        predictor = InnovationPredictor()
        result = predictor.predict_growth(90, 1000000000)
        assert isinstance(result, float)
        assert result != 0.0

# ==========================================
# 2. UNIT TEST: SERVICES (API MOCKING)
# ==========================================
class TestServices:
    @patch('services.requests.get')
    def test_fetch_api_success(self, mock_get):
        from services import DataNexus
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_res
        
        nexus = DataNexus({})
        result = nexus.fetch_api("http://fakeurl.com")
        assert result == {"status": "ok"}

# ==========================================
# 3. INTEGRATION TEST: ROUTES
# ==========================================
class TestRoutes:
    def test_index_page(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert b"TeknoAtlas" in response.data

    @patch('app.nexus.get_countries')
    @patch('app.nexus.get_gdp')
    @patch('app.nexus.get_rd_expenditure')
    @patch('app.nexus.get_inflation')
    @patch('app.nexus.get_internet_usage')
    def test_analysis_page_robust(self, mock_internet, mock_inflation, mock_rd, mock_gdp, mock_countries, client):
        # Setup Mock Data
        mock_countries.return_value = [
            {'cca3': 'IDN', 'name': {'common': 'Indonesia'}, 'population': 273000000, 'flags': {'png': ''}, 'region': 'Asia'}
        ]
        mock_gdp.return_value = 1000000000000
        mock_rd.return_value = 0.5
        mock_inflation.return_value = 3.5
        mock_internet.return_value = 75.0
        
        # Penting: Bersihkan cache
        from app import cache
        with flask_app.app_context():
            cache.clear()

        response = client.get('/analysis')
        html = response.data.decode('utf-8')
        
        assert response.status_code == 200
        assert "Indonesia" in html
        assert "75.0%" in html
        assert "3.5%" in html

    def test_country_detail_404(self, client):
        response = client.get('/country/XYZ')
        assert response.status_code == 404

    def test_country_detail_lowercase(self, client):
        from app import cache
        with flask_app.app_context():
            cache.clear()
        response = client.get('/country/idn')
        assert response.status_code == 200
        assert b"Indonesia" in response.data
