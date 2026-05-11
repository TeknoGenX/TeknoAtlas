import requests
import logging
import json

logger = logging.getLogger("TeknoNexus-ML")

class DataNexus:
    def __init__(self, tech_database):
        self.tech_database = tech_database
        self.endpoints = {
            "countries": "https://restcountries.com/v3.1/all?fields=name,flags,population,cca3,area,currencies",
            "worldbank": "https://api.worldbank.org/v2/country/{iso3}/indicator/{indicator}?format=json&mrv=1"
        }

    def fetch_api(self, url):
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request Error for {url}: {e}")
            return None

    def get_countries(self):
        """Ambil daftar negara dari API RestCountries."""
        raw = self.fetch_api(self.endpoints["countries"])
        if not raw: return []
        target = self.tech_database.keys()
        return [c for c in raw if c.get('cca3') in target]

    def get_indicator(self, iso3, indicator):
        """Ambil data indikator spesifik dari World Bank."""
        url = self.endpoints["worldbank"].format(iso3=iso3, indicator=indicator)
        data = self.fetch_api(url)
        try:
            if data and len(data) > 1 and data[1] and 'value' in data[1][0]:
                val = data[1][0]['value']
                return round(float(val), 2) if val is not None else 0
            return 0
        except (IndexError, KeyError, TypeError, ValueError):
            return 0

    def get_gdp(self, iso3):
        return self.get_indicator(iso3, "NY.GDP.MKTP.CD")

    def get_rd_expenditure(self, iso3):
        """Research and development expenditure (% of GDP)."""
        return self.get_indicator(iso3, "GB.XPD.RSDV.GD.ZS")

    def get_inflation(self, iso3):
        """Inflation, consumer prices (annual %)."""
        return self.get_indicator(iso3, "FP.CPI.TOTL.ZG")

    def get_internet_usage(self, iso3):
        """Individuals using the Internet (% of population)."""
        return self.get_indicator(iso3, "IT.NET.USER.ZS")

    def get_hitech_exports(self, iso3):
        """High-technology exports (% of manufactured exports)."""
        return self.get_indicator(iso3, "TX.VAL.TECH.ZS.DG")

    def get_scientific_journals(self, iso3):
        """Scientific and technical journal articles."""
        return self.get_indicator(iso3, "IP.JRN.ARTC.SC")

    def get_unemployment(self, iso3):
        """Unemployment, total (% of total labor force) (modeled ILO estimate)."""
        return self.get_indicator(iso3, "SL.UEM.TOTL.ZS")

    def get_patents(self, iso3):
        """Patent applications, residents."""
        return self.get_indicator(iso3, "IP.PAT.RESD")

    def get_fdi(self, iso3):
        """Foreign direct investment, net inflows (% of GDP)."""
        return self.get_indicator(iso3, "BX.KLT.DINV.WD.GD.ZS")

    def get_ip_receipts(self, iso3):
        """Charges for the use of intellectual property, receipts (BoP, current US$)."""
        return self.get_indicator(iso3, "BX.GSR.ROYL.CD")

    def get_tech_news(self):
        """Ambil berita teknologi dari beberapa sumber publik."""
        news_sources = [
            {
                "url": "https://saurav.tech/NewsAPI/top-headlines/category/technology/us.json",
                "parser": self._parse_saurav
            },
            {
                "url": "https://dev.to/api/articles?per_page=5&top=7",
                "parser": self._parse_devto
            },
            {
                "url": "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=5",
                "parser": self._parse_hn
            }
        ]
        
        all_news = []
        for source in news_sources:
            data = self.fetch_api(source["url"])
            if data:
                all_news.extend(source["parser"](data))
        
        # Sortir berdasarkan tanggal (jika ada) atau acak
        return all_news[:15]

    def _parse_saurav(self, data):
        results = []
        for art in data.get('articles', [])[:5]:
            results.append({
                "source": art.get('source', {}).get('name', 'NewsAPI'),
                "date": art.get('publishedAt', '')[:10],
                "title": art.get('title'),
                "summary": art.get('description'),
                "url": art.get('url')
            })
        return results

    def _parse_devto(self, data):
        results = []
        for art in data[:5]:
            results.append({
                "source": "Dev.to",
                "date": art.get('published_at', '')[:10],
                "title": art.get('title'),
                "summary": art.get('description'),
                "url": art.get('url')
            })
        return results

    def _parse_hn(self, data):
        results = []
        for hit in data.get('hits', [])[:5]:
            results.append({
                "source": "Hacker News",
                "date": hit.get('created_at', '')[:10],
                "title": hit.get('title'),
                "summary": f"Points: {hit.get('points')} | Author: {hit.get('author')}",
                "url": hit.get('url') if hit.get('url') else f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            })
        return results

    def _parse_spaceflight(self, data):
        results = []
        for art in data.get('results', [])[:5]:
            results.append({
                "source": art.get('news_site', 'Spaceflight News'),
                "date": art.get('published_at', '')[:10],
                "title": art.get('title'),
                "summary": art.get('summary'),
                "url": art.get('url')
            })
        return results

    def get_country_detail(self, iso3):
        """Ambil detail negara dari database internal dan gabungkan dengan data bendera serta ekonomi."""
        if iso3 not in self.tech_database:
            return None
            
        # Ambil data dasar dari API RestCountries
        url = f"https://restcountries.com/v3.1/alpha/{iso3}?fields=name,flags,population,region,subregion,capital,currencies"
        raw = self.fetch_api(url)
        
        detail = self.tech_database[iso3].copy()
        if raw:
            currency_code = list(raw.get('currencies', {}).keys())[0] if raw.get('currencies') else "N/A"
            currency_name = raw.get('currencies', {}).get(currency_code, {}).get('name', "N/A")
            
            detail.update({
                "flag": raw.get('flags', {}).get('png'),
                "official_name": raw.get('name', {}).get('official'),
                "population": raw.get('population'),
                "region": raw.get('region'),
                "subregion": raw.get('subregion'),
                "capital": raw.get('capital', [None])[0],
                "currency": f"{currency_name} ({currency_code})"
            })
        return detail
