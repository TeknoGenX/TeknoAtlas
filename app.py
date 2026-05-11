from flask import Flask, render_template
import logging
import json
from concurrent.futures import ThreadPoolExecutor
from flask_caching import Cache
from ml_engine import InnovationPredictor
from services import DataNexus

# ==========================================
# 1. CORE SETUP & DATA LOADING
# ==========================================
app = Flask(__name__)

# Konfigurasi Caching
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 3600}) # Cache 1 jam

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("TeknoNexus-ML")

def load_tech_database():
    try:
        with open('data/tech_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Tech database file not found!")
        return {}

TECH_DATABASE = load_tech_database()
predictor = InnovationPredictor()
nexus = DataNexus(TECH_DATABASE)

# ==========================================
# 2. ROUTES
# ==========================================
@app.route('/')
@cache.cached(timeout=86400) # Cache 24 jam untuk daftar negara (data statis)
def index():
    countries_raw = nexus.get_countries()
    
    # Gabungkan data API dengan data internal TECH_DATABASE
    enriched_countries = []
    for c in countries_raw:
        iso3 = c.get('cca3')
        if iso3 in TECH_DATABASE:
            c_data = c.copy()
            c_data.update({
                'desc': TECH_DATABASE[iso3]['desc'],
                'maturity': TECH_DATABASE[iso3]['maturity']
            })
            enriched_countries.append(c_data)
            
    enriched_countries.sort(key=lambda x: (x['cca3'] != 'IDN', x['name']['common']))
    return render_template('index.html', countries=enriched_countries)

@app.route('/analysis')
@cache.cached(timeout=3600) # Cache 1 jam untuk analisis (menghemat API calls & ML)
def global_analysis():
    countries_raw = nexus.get_countries()
    target_iso3 = list(TECH_DATABASE.keys())
    
    # Ambil data multi-indicator secara paralel
    def fetch_all_data(iso3):
        return {
            "iso3": iso3,
            "gdp": nexus.get_gdp(iso3),
            "rd": nexus.get_rd_expenditure(iso3),
            "inflation": nexus.get_inflation(iso3),
            "internet": nexus.get_internet_usage(iso3)
        }

    with ThreadPoolExecutor(max_workers=5) as executor:
        economic_data = list(executor.map(fetch_all_data, target_iso3))
    
    results = []
    for econ in economic_data:
        iso3 = econ['iso3']
        api_c = next((c for c in countries_raw if c['cca3'] == iso3), None)
        if api_c:
            maturity = TECH_DATABASE[iso3]['maturity']
            forecast_growth = predictor.predict_growth(maturity, econ['gdp'])
            
            results.append({
                "name": api_c['name']['common'],
                "gdp": econ['gdp'],
                "population": api_c['population'],
                "score": maturity,
                "rd": econ['rd'],
                "inflation": econ['inflation'],
                "internet": econ['internet'],
                "forecast": forecast_growth,
                "iso3": iso3
            })
            
    results.sort(key=lambda x: x['score'], reverse=True)
    return render_template('analysis.html', data=results)

@app.route('/country/<iso3>')
@cache.memoize(timeout=86400)
def country_detail(iso3):
    detail = nexus.get_country_detail(iso3)
    if not detail:
        return render_template('index.html', error="Negara tidak ditemukan dalam basis data inovasi."), 404
    
    # Ambil data ekonomi & teknologi tambahan secara paralel
    with ThreadPoolExecutor(max_workers=6) as executor:
        f_gdp = executor.submit(nexus.get_gdp, iso3)
        f_rd = executor.submit(nexus.get_rd_expenditure, iso3)
        f_inflation = executor.submit(nexus.get_inflation, iso3)
        f_internet = executor.submit(nexus.get_internet_usage, iso3)
        f_hitech = executor.submit(nexus.get_hitech_exports, iso3)
        f_journals = executor.submit(nexus.get_scientific_journals, iso3)
        f_unemployment = executor.submit(nexus.get_unemployment, iso3)
        
        gdp = f_gdp.result()
        rd = f_rd.result()
        inflation = f_inflation.result()
        internet = f_internet.result()
        hitech = f_hitech.result()
        journals = f_journals.result()
        unemployment = f_unemployment.result()

    forecast = predictor.predict_growth(detail['maturity'], gdp)
    
    return render_template('detail.html', 
                           country=detail, 
                           gdp=gdp, 
                           rd=rd, 
                           inflation=inflation, 
                           internet=internet,
                           hitech=hitech,
                           journals=journals,
                           unemployment=unemployment,
                           forecast=forecast)

@app.route('/map')
def show_map():
    # Data hub inovasi dunia yang diperluas
    hubs = [
        {"lat": -6.2088, "lng": 106.8456, "name": "Jakarta Tech Hub", "country": "Indonesia", "focus": "Fintech & E-commerce"},
        {"lat": 37.7749, "lng": -122.4194, "name": "Silicon Valley", "country": "USA", "focus": "AI & Semiconductors"},
        {"lat": 22.5431, "lng": 114.0579, "name": "Shenzhen Innovation Zone", "country": "China", "focus": "Hardware & EV"},
        {"lat": 35.6762, "lng": 139.6503, "name": "Tokyo Robotics Cluster", "country": "Japan", "focus": "Robotics & Precision Eng"},
        {"lat": 52.5200, "lng": 13.4050, "name": "Berlin Startup Scene", "country": "Germany", "focus": "SaaS & Industry 4.0"},
        {"lat": 37.4000, "lng": 127.1000, "name": "Pangyo Techno Valley", "country": "South Korea", "focus": "Memories & Game Dev"},
        {"lat": 52.2053, "lng": 0.1218, "name": "Cambridge Science Park", "country": "UK", "focus": "Deeptech & AI"},
        {"lat": 32.0853, "lng": 34.7818, "name": "Silicon Wadi", "country": "Israel", "focus": "Cybersecurity"},
        {"lat": 1.2902, "lng": 103.8519, "name": "one-north", "country": "Singapore", "focus": "Smart Nation & Foodtech"},
        {"lat": 12.9716, "lng": 77.5946, "name": "Bangalore", "country": "India", "focus": "IT Services & Space"},
        {"lat": 48.8566, "lng": 2.3522, "name": "Station F", "country": "France", "focus": "AI & Green Tech"}
    ]
    return render_template('map.html', hubs=hubs)

@app.route('/news')
@cache.cached(timeout=3600)
def show_news():
    news_items = nexus.get_tech_news()
    return render_template('news.html', news=news_items)

if __name__ == '__main__':
    app.run(debug=False)
