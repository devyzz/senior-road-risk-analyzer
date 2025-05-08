#──────────────────────────────────────────────────────────────
#  횡단보도 데이터 수집 및 전처리
#
# - 내용 : 2023년도 서울시 자치구별 횡단보도 데이터 전저리
# - 데이터 : 서울특별시_자치구별 신호등 및 횡단보도 위치 및 현황_20230530.xlsx
# - 출처 : 서울 열린데이터 광장
# - 도구 : pandas
# - 작성자 : 이주안
# - 작성일 : 2025.05.07
# - 수정자 : 이주안
# - 수정일 : 2025.05.08
# - 수정내용 :  
#   - 자치구별 신호등 개수 집계 및 시각화
#   - 시각화 코드 제거, x,y 좌표 변환 추가, 파일 저장 로직 생성 
# ──────────────────────────────────────────────────────────────

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pyproj import Transformer
import time

def convert_coordinates(row, transformer):
    try:
        lng, lat = transformer.transform(row["X좌표"], row["Y좌표"])
        return pd.Series({"위도": lat, "경도": lng})
    except:
        return pd.Series({"위도": None, "경도": None})

# 한글 폰트 설정 (예: Apple 기본 폰트 사용)
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False
# 파일 경로 및 데이터 로드, 헤더는 3번째 줄 (index 2)
file_path = "./data/raw/서울특별시_자치구별 신호등 및 횡단보도 위치 및 현황_20230530.xlsx"
df_signal = pd.read_excel(file_path, engine='openpyxl', header=2)
# 첫번째 열(A열)이 의미 없는 빈 열인 경우 삭제
if df_signal.columns[0].startswith('Unnamed'):
    df_signal = df_signal.drop(columns=[df_signal.columns[0]])
    df_signal.columns = ['순번', '자치구', '관리번호', '횡단보도종류', '주소', '교차로명', 'X좌표', 'Y좌표', '도로구분']
# 인덱스 재정렬
df_signal.reset_index(drop=True, inplace=True)
time.sleep(1)

# 좌표 컬럼을 숫자형으로 먼저 변환 (변환 불가한 값은 NaN 처리)
df_signal['X좌표'] = pd.to_numeric(df_signal['X좌표'], errors='coerce')
df_signal['Y좌표'] = pd.to_numeric(df_signal['Y좌표'], errors='coerce')
# 좌표 변환기: TM → WGS84
time.sleep(1)
transformer = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)

# 유효한 좌표에 대해서만 변환
mask = df_signal['X좌표'].notna() & df_signal['Y좌표'].notna()
df_signal.loc[mask, ['위도', '경도']] = df_signal.loc[mask].apply(
    lambda row: convert_coordinates(row, transformer),
    axis=1
)
# '구분' 컬럼 추가 및 값 할당
df_signal["구분"] = "횡단보도"
# 컬럼 순서 재정렬
df_signal = df_signal[["구분", "위도", "경도"]]
# 저장
output_path = "./data/external/crosswalk_2023_cleaned.csv"
df_signal.to_csv(output_path, index=False)
print(f"CSV 저장 완료: {output_path}")