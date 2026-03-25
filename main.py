"""
HanziPulse - main.py
전체 파이프라인 실행
"""

import sys
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("HanziPulse")


def run_collect():
    from collector import run
    log.info("=== 데이터 수집 시작 ===")
    run()

def run_analyze():
    import glob
    from analyzer import run
    raw_dir = Path("data/raw")
    trends_files = sorted(glob.glob(str(raw_dir / "trends_*.csv")))
    etsy_files = sorted(glob.glob(str(raw_dir / "etsy_tags_*.json")))
    trends_csv = trends_files[-1] if trends_files else None
    etsy_json = etsy_files[-1] if etsy_files else None
    if not trends_csv:
        log.warning("Trends 데이터 없음 — collect 먼저 실행하세요")
        return
    log.info("=== 분석 시작 ===")
    run(trends_csv=trends_csv, etsy_tags_json=etsy_json)

def run_dashboard():
    import subprocess
    log.info("=== 대시보드 시작 ===")
    subprocess.run(["streamlit", "run", "src/visualizer.py"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HanziPulse")
    parser.add_argument(
        "command",
        choices=["collect", "analyze", "dashboard", "all"],
        help="실행할 커맨드"
    )
    args = parser.parse_args()

    if args.command == "collect":
        run_collect()
    elif args.command == "analyze":
        run_analyze()
    elif args.command == "dashboard":
        run_dashboard()
    elif args.command == "all":
        run_collect()
        run_analyze()
        run_dashboard()
