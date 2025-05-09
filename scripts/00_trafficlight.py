#──────────────────────────────────────────────────────────────
#  신호등 데이터 수집 및 전처리
#
# - 내용 : 2023년도 서울시 자치구별 신호등 데이터 전저리
# - 데이터 : 서울시 신호등 관련 정보.csv
# - 출처 : 열린데이터 광장 
# - 도구 : 
# - 작성자 : 이주안
# - 작성일 : 2025.05.08
# - 수정자 : 이주안
# - 수정일 : 2025.05.09
# - 수정내용 :  
#   - 공공 데이터 수집하려 했으나, 특정 서울시 동작구 데이터만 나와서 데이터 기각
#   - 데이터 수집 및 전처리
#   - 차량 진행 제어를 직접적으로 하는 신호등만 수집 
#     테이블 정의서 신호등 종류 코드 2,4,5,6,21
#   - 중복값 제거
# ──────────────────────────────────────────────────────────────

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pyproj import Transformer
import time
import folium


# 한글 폰트 설정 (예: Apple 기본 폰트 사용)
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False
# 파일 경로 및 데이터 로드
file_path = "./data/raw/서울시 신호등 관련 정보.csv"

# 데이터 로드
df = pd.read_csv(file_path, encoding='euc-kr')
df = df[["부착대관리번호","신호등종류", "X좌표", "Y좌표"]]
df = df[df["신호등종류"].isin([2.0, 4.0, 5.0, 6.0, 21.0])]
df = df.drop_duplicates(subset=["X좌표", "Y좌표"])
print(df.head())
output_path="./data/processed/trafficlight_2023.csv"
df.to_csv(output_path, index=False)
print(f"CSV 저장 완료: {output_path}")
