# ⛩️ HanziPulse

HANZI 브랜드를 위한 Korean Market Intelligence 툴.
Google Trends + Etsy API 기반 키워드 트렌드 & 연관관계 분석.

## 설치

```bash
pip install -r requirements.txt
cp .env.example .env
# .env 파일에 ETSY_API_KEY 입력
```

## 실행

```bash
# 데이터 수집
python main.py collect

# 분석
python main.py analyze

# 대시보드
python main.py dashboard

# 전체 한번에
python main.py all
```

## 프로젝트 구조

```
HanziPulse/
├── main.py              # 진입점
├── config.yaml          # 키워드 설정
├── requirements.txt
├── .env.example
├── src/
│   ├── collector.py     # 데이터 수집 (Google Trends + Etsy)
│   ├── analyzer.py      # 연관관계 분석 (Co-occurrence + Network)
│   └── visualizer.py    # Streamlit 대시보드
├── data/
│   ├── raw/             # 수집 원본 데이터
│   └── processed/       # 분석 결과
└── notebooks/           # 탐색적 분석용
```

## 데이터 소스

| 소스 | 용도 | 비용 |
|------|------|------|
| Google Trends | 키워드 시계열 트렌드 | 무료 |
| Etsy Open API | Listing 태그 수집 | 무료 |
