# 🛣️ Senior Road Risk Analyzer

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Notebook-Jupyter-orange)](./notebooks)
[![Data Project](https://img.shields.io/badge/Project-Type%3A%20Data-blueviolet)]()
[![Map Visualization](https://img.shields.io/badge/Map-Folium-green)](https://python-visualization.github.io/folium/)
![Last Update](https://img.shields.io/github/last-commit/devyzz/senior-road-risk-analyzer)

> 고령 운전자 교통사고 데이터를 중심으로, 도로 환경 및 시설 요소와의 연관성을 분석하고  
> 이를 기반으로 도로 구간별 **위험도를 정량화 및 시각화**하는 데이터 기반 도로 안전 평가 시스템입니다.

---

## 📌 개요

- **목표**  
  고령 운전자 사고가 자주 발생하는 도로의 공통 특성과 환경 요소를 분석하여,  
  **사전 예방형 도로 안전관리 지표**를 제공하는 것을 목표로 합니다.

- **활용 데이터**
  - 2021~2023 서울시 교통사고 정보 (TAAS, 서울열린데이터광장)
  - 보호구역 / 신호등 / 횡단보도 위치 데이터 (OpenAPI)
  - 도로 속도, 차선수, 도로 길이 등 환경 데이터

---

## 👥 팀원 소개

| [김예지](https://github.com/devyzz) | [김정은](https://github.com/kje0316) | [이주안](https://github.com/HI-JUAN) |
| :---------------------------------- | :---------------------------------- | :---------------------------------- |
|          |   | |

---

## 🔧 주요 기능

| 기능 | 설명 |
|------|------|
| 🚦 도로 환경 통합 | 보호구역, 신호등, 횡단보도, 교차로 등의 위치 데이터를 사고 정보와 병합 |
| 📊 SHAP 기반 해석 | XGBoost 모델을 활용하여 고령운전자 사고에 영향을 주는 변수 가중치 산출 |
| 🛣️ 도로 위험도 점수화 | SHAP 값을 기반으로 각 도로 링크별 위험도 점수 산정 |
| 🗺️ 대시보드 시각화 | Folium을 활용한 지도 기반 위험도 시각화 및 구간별 분석 제공 |

---

## 🗂️ 폴더 구조

```bash
senior-road-risk-analyzer/
├── data/                          # 수집된 데이터
│   ├── external/                  # 외부 API로 수집한 위치/환경 데이터
│   ├── processed/                 # 전처리 및 통합 데이터
│   └── raw/                       # 수집 직후 원본 데이터
│
├── docs/                          # 프로젝트 문서
│   ├── 참가서류/                   # 공모전 제출용 문서 (기획서, 별첨자료 등)
│   ├── MERGE_GUIDE.md             # 데이터 병합 방법 정리
│   └── TEAM_GUIDE.md              # 팀 작업 방식 안내
│
├── notebooks/                     # 실험 및 분석 노트북
│   ├── 사고데이터 보호구역병합 정확성검증.ipynb  
│   ├── 위험요소별 가중치 검증 및 도로시각화.ipynb  
│   └── SHAP 기반 고령운전자 도로 위험 요인 분석 및 해석.ipynb  
│
├── scripts/                       # 실행 스크립트
│   ├── utils/                     # 공통 함수
│   │   ├── CONSTANTS.py
│   │   └── GEO_UTILS.py
│   ├── collect_accident_data.py
│   ├── collect_reference_data.py
│   └── preprocess_and_merge.py
│
├── requirements.txt               # Python 의존성
├── README.md                      # 프로젝트 소개
└── .gitignore                     # Git 무시 파일 목록
```

## 📑 참고자료
[EuroRAP 도로 평가 모델](https://en.wikipedia.org/wiki/EuroRAP)<br>
[Systemwide Risk Assessment Guide (FHWA)](https://highways.dot.gov/sites/fhwa.dot.gov/files/2024-10/Systemwide%20Risk%20Assessment%20How-To%20Guide.pdf)