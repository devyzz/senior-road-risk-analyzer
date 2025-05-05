# 🛣️ Senior Road Risk Analyzer
>  고령 운전자 사고데이터 및 도로 특성 데이터를 기반으로 도로 위험도를 분석하고 시각화하는 프로젝트입니다.

- 🧑‍🧒‍🧒 **프로젝트 인원** : 3명
- 🗓️ **프로젝트 기간** : 2025.04.23 ~ 2025.05.23


## 👥 팀원소개 
| [김예지](https://github.com/devyzz)   | [김정은](https://github.com/kje0316)  | [이주안](https://github.com/HI-JUAN)   |
| :-------------------------------------------- | :---------------------------------------- | :---------------------------------------------- |


## 🛣️ 주요 기능
- 교통사고 및 도로데이터 통합
- 도로별 위험도 점수 산출 (SHAP 등 사용)
- 대시보드로 시각화
- API 서버를 통한 실시간 경로점수 웹제작

## 🛣️ 폴더 구조
```bash
senior-road-risk-analyzer/
├── 📁data/                      # 수집한 원본 및 전처리 데이터
│   ├── 📁raw/                     # 원본 데이터
│   ├── 📁processed/               # 전처리 완료된 데이터
│   └── 📁external/                # 외부 공공데이터
│
├── 📁notebooks/                 # 분석 및 실험용 Jupyter 노트북
│   ├── example.ipynb              
│
├── 📁scripts/                   # 실행용 파이썬 스크립트
│   ├── taas_accident_api.py     # TAAS GIS분석 페이지 데이터 수집 크롤링 스크립트
│
├── 📁webapi/                    # FastAPI 서버 코드
│   ├── main.py
│
├── requirements.txt           # 필요한 라이브러리 목록
├── README.md                  # 프로젝트 소개 문서
└── .gitignore                 # Git에 포함되지 않을 파일 목록
```
