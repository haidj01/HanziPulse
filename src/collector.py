"""
HanziPulse - collector.py
Google Trends + Etsy API 데이터 수집
"""

import os
import time
import json
import yaml
import logging
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from pytrends.request import TrendReq

# ── 로깅 설정 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("HanziPulse")

# ── 설정 로드 ──────────────────────────────────────────────
CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def get_all_keywords(config: dict) -> list:
    """config의 모든 카테고리 키워드를 flat list로 반환"""
    all_kw = []
    for category, keywords in config["keywords"].items():
        all_kw.extend(keywords)
    return all_kw

def get_keywords_by_category(config: dict) -> dict:
    return config["keywords"]


# ── Google Trends 수집 ─────────────────────────────────────
class GoogleTrendsCollector:
    def __init__(self, config: dict):
        self.cfg = config["settings"]["trends"]
        self.pytrends = TrendReq(hl=self.cfg["language"], tz=360)
        self.timeframe = self.cfg["timeframe"]
        self.geo = self.cfg["geo"]

    def fetch_interest_over_time(self, keywords: list) -> pd.DataFrame:
        """
        키워드 리스트의 시계열 트렌드 수집
        pytrends는 한 번에 최대 5개 키워드만 허용 → 배치 처리
        """
        all_dfs = []
        batches = [keywords[i:i+5] for i in range(0, len(keywords), 5)]

        for i, batch in enumerate(batches):
            log.info(f"Trends 수집 배치 {i+1}/{len(batches)}: {batch}")
            try:
                self.pytrends.build_payload(
                    batch,
                    timeframe=self.timeframe,
                    geo=self.geo
                )
                df = self.pytrends.interest_over_time()
                if not df.empty:
                    df = df.drop(columns=["isPartial"], errors="ignore")
                    all_dfs.append(df)
            except Exception as e:
                log.warning(f"배치 실패 {batch}: {e}")
            time.sleep(2)  # rate limit 방지

        if all_dfs:
            return pd.concat(all_dfs, axis=1)
        return pd.DataFrame()

    def fetch_related_queries(self, keywords: list) -> dict:
        """키워드별 연관 검색어 수집"""
        results = {}
        batches = [keywords[i:i+5] for i in range(0, len(keywords), 5)]

        for batch in batches:
            try:
                self.pytrends.build_payload(
                    batch,
                    timeframe=self.timeframe,
                    geo=self.geo
                )
                related = self.pytrends.related_queries()
                for kw in batch:
                    if kw in related:
                        top = related[kw].get("top")
                        rising = related[kw].get("rising")
                        results[kw] = {
                            "top": top.to_dict("records") if top is not None else [],
                            "rising": rising.to_dict("records") if rising is not None else []
                        }
            except Exception as e:
                log.warning(f"Related queries 실패 {batch}: {e}")
            time.sleep(2)

        return results


# ── Etsy API 수집 ──────────────────────────────────────────
class EtsyCollector:
    BASE_URL = "https://openapi.etsy.com/v3/application"

    def __init__(self, config: dict, api_key: str):
        self.cfg = config["settings"]["etsy"]
        self.api_key = api_key
        self.headers = {"x-api-key": api_key}

    def search_listings(self, keyword: str) -> list:
        """키워드로 Etsy listing 검색"""
        url = f"{self.BASE_URL}/listings/active"
        params = {
            "keywords": keyword,
            "limit": self.cfg["max_listings"],
            "sort_on": "score",
            "sort_order": "desc",
            "includes": ["tags", "images"]
        }
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
        except Exception as e:
            log.warning(f"Etsy 검색 실패 [{keyword}]: {e}")
            return []

    def extract_tags(self, listings: list) -> list:
        """listing에서 태그 추출"""
        tags = []
        for listing in listings:
            tags.extend(listing.get("tags", []))
        return tags

    def fetch_keyword_tags(self, keywords: list) -> dict:
        """키워드별 Etsy 태그 수집"""
        results = {}
        for kw in keywords:
            log.info(f"Etsy 수집: {kw}")
            listings = self.search_listings(kw)
            tags = self.extract_tags(listings)
            results[kw] = {
                "listing_count": len(listings),
                "tags": tags
            }
            time.sleep(1)  # rate limit 방지
        return results


# ── 저장 ──────────────────────────────────────────────────
class DataSaver:
    def __init__(self, base_dir: str = "data"):
        self.raw_dir = Path(base_dir) / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def save_trends(self, df: pd.DataFrame):
        if df.empty:
            log.warning("Trends 데이터 없음, 저장 스킵")
            return
        path = self.raw_dir / f"trends_{self.timestamp}.csv"
        df.to_csv(path)
        log.info(f"Trends 저장: {path}")

    def save_related_queries(self, data: dict):
        path = self.raw_dir / f"related_queries_{self.timestamp}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log.info(f"Related queries 저장: {path}")

    def save_etsy_tags(self, data: dict):
        path = self.raw_dir / f"etsy_tags_{self.timestamp}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log.info(f"Etsy tags 저장: {path}")


# ── 메인 실행 ──────────────────────────────────────────────
def run():
    config = load_config()
    keywords = get_all_keywords(config)
    saver = DataSaver()

    # 1. Google Trends
    log.info("=== Google Trends 수집 시작 ===")
    trends_collector = GoogleTrendsCollector(config)
    trends_df = trends_collector.fetch_interest_over_time(keywords)
    saver.save_trends(trends_df)

    related = trends_collector.fetch_related_queries(keywords)
    saver.save_related_queries(related)

    # 2. Etsy API (API 키 필요)
    etsy_api_key = os.getenv("ETSY_API_KEY")
    if etsy_api_key:
        log.info("=== Etsy 수집 시작 ===")
        etsy_collector = EtsyCollector(config, etsy_api_key)
        etsy_data = etsy_collector.fetch_keyword_tags(keywords)
        saver.save_etsy_tags(etsy_data)
    else:
        log.warning("ETSY_API_KEY 환경변수 없음 → Etsy 수집 스킵")

    log.info("=== 수집 완료 ===")


if __name__ == "__main__":
    run()
