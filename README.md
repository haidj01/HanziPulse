# ⛩️ HanziPulse

**Korean Market Intelligence for HANZI Brand**
**HANZI 브랜드를 위한 한국 시장 인텔리전스 툴**

Google Trends + Etsy API 기반 키워드 트렌드 & 연관관계 분석 도구
A keyword trend and relationship analysis tool powered by Google Trends + Etsy API

---

## 목차 / Table of Contents

- [소개 / Introduction](#소개--introduction)
- [설치 / Installation](#설치--installation)
- [설정 / Configuration](#설정--configuration)
- [실행 / Usage](#실행--usage)
- [프로젝트 구조 / Project Structure](#프로젝트-구조--project-structure)
- [데이터 소스 / Data Sources](#데이터-소스--data-sources)

---

## 소개 / Introduction

**한국어**
HanziPulse는 HANZI 스트리트웨어 브랜드의 시장 수요를 분석하기 위한 개인용 리서치 툴입니다.
한국 전통 문화 및 스트리트웨어 관련 키워드의 트렌드를 추적하고, 키워드 간 연관관계를 네트워크 그래프로 시각화합니다.

**English**
HanziPulse is a personal market research tool for analyzing demand related to the HANZI streetwear brand.
It tracks keyword trends around Korean traditional culture and streetwear fashion, and visualizes keyword relationships as an interactive network graph.

---

## 설치 / Installation

```bash
# 저장소 클론 / Clone repository
git clone https://github.com/your-repo/HanziPulse.git
cd HanziPulse

# 패키지 설치 / Install dependencies
pip install -r requirements.txt

# 환경변수 설정 / Set up environment variables
cp .env.example .env
# .env 파일에 ETSY_API_KEY 입력
# Edit .env and add your ETSY_API_KEY
```

---

## 설정 / Configuration

**한국어**
`config.yaml`에서 추적할 키워드와 수집 설정을 변경할 수 있습니다.

**English**
Edit `config.yaml` to customize tracked keywords and collection settings.

```yaml
keywords:
  traditional_korean:   # 한국 전통 키워드 / Korean traditional keywords
  korean_objects:       # 한국 전통 물건 / Korean traditional objects
  streetwear_fashion:   # 스트리트웨어 / Streetwear fashion
  cultural_fusion:      # 문화 융합 / Cultural fusion
  korean_cities:        # 한국 주요 도시 / Korean cities
  korean_travel:        # 한국 여행 / Korean travel

settings:
  trends:
    timeframe: "today 6-m"  # 수집 기간 / Collection period
    geo: "US"               # 타겟 지역 / Target region
```

**Etsy API 키 발급 / Getting Etsy API Key**

한국어: [etsy.com/developers](https://www.etsy.com/developers) 에서 계정 로그인 후 Private App 생성 → 무료 즉시 발급 (심사 후 승인)

English: Log in at [etsy.com/developers](https://www.etsy.com/developers), create a Private App → free, approved after review

---

## 실행 / Usage

```bash
# 데이터 수집 / Collect data
python main.py collect

# 분석 실행 / Run analysis
python main.py analyze

# 대시보드 실행 / Launch dashboard
python main.py dashboard

# 전체 파이프라인 / Run full pipeline
python main.py all
```

**대시보드 페이지 / Dashboard Pages**

| 페이지 / Page | 내용 / Content |
|---|---|
| 📈 Trends | 시계열 트렌드, 상위/상승 키워드, 상관관계 히트맵 / Time-series trends, top/rising keywords, correlation heatmap |
| 🔗 Network | 브릿지 키워드, 네트워크 그래프, 클러스터 / Bridge keywords, network graph, clusters |
| 🏷️ Tag Analysis | 키워드별 listing 수, 태그 탐색기 / Listing counts per keyword, tag explorer |

---

## 프로젝트 구조 / Project Structure

```
HanziPulse/
├── main.py              # 진입점 / Entry point
├── config.yaml          # 키워드 & 설정 / Keywords & settings
├── requirements.txt     # 패키지 목록 / Dependencies
├── .env.example         # 환경변수 예시 / Environment variable template
├── .gitignore
├── README.md
├── src/
│   ├── collector.py     # 데이터 수집 / Data collection (Google Trends + Etsy)
│   ├── analyzer.py      # 연관관계 분석 / Keyword relationship analysis
│   └── visualizer.py    # Streamlit 대시보드 / Dashboard
├── data/
│   ├── raw/             # 수집 원본 데이터 / Raw collected data
│   └── processed/       # 분석 결과 / Analysis results
└── notebooks/           # 탐색적 분석 / Exploratory analysis
```

---

## 데이터 소스 / Data Sources

| 소스 / Source | 용도 / Purpose | 비용 / Cost |
|---|---|---|
| Google Trends | 키워드 시계열 트렌드 / Keyword time-series trends | 무료 / Free |
| Etsy Open API | Listing 태그 수집 / Listing tag collection | 무료 / Free |

---

*Built for HANZI — Korean Traditional Culture × Streetwear*
