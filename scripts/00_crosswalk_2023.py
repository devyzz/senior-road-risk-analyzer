#──────────────────────────────────────────────────────────────
#  횡단보도 데이터 수집 및 전처리
#
# - 내용 : 2023년도 서울시 자치구별 신호등 개수 집계 및 시각화
# - 데이터 : 서울특별시_자치구별 신호등 및 횡단보도 위치 및 현황_20230530.xlsx
# - 출처 : 서울 열린데이터 광장
# - 도구 : pandas, matplotlib, folium
# - 작성자 : 이주안
# - 작성일 : 2025.05.07
# - 수정자 : 이주안
# - 수정일 : 2025.05.08
# - 수정내용 :  
#   - 자치구별 신호등 개수 집계 및 시각화
#   - 시각화 코드 제거, x,y 좌표 변환 추가
# ──────────────────────────────────────────────────────────────

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import folium
from pyproj import Transformer
import time

# 한글 폰트 설정 (예: Apple 기본 폰트 사용)
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# 파일 경로 및 데이터 로드, 헤더는 3번째 줄 (index 2)
file_path = "/Users/leejuan/Desktop/교통국토경진대회/02. data/서울특별시_자치구별 신호등 및 횡단보도 위치 및 현황_20230530.xlsx"
df_signal = pd.read_excel(file_path, engine='openpyxl', header=2)
# 첫번째 열(A열)이 의미 없는 빈 열인 경우 삭제
if df_signal.columns[0].startswith('Unnamed'):
    df_signal = df_signal.drop(columns=[df_signal.columns[0]])
    df_signal.columns = ['순번', '자치구', '관리번호', '횡단보도종류', '주소', '교차로명', 'X좌표', 'Y좌표', '도로구분']
# 인덱스 재정렬
df_signal.reset_index(drop=True, inplace=True)
print("📁 데이터 로딩 완료")
time.sleep(1)
print(df_signal.columns)
print(len(df_signal.columns))
print(df_signal[['X좌표', 'Y좌표']].head(10))


# 좌표 컬럼을 숫자형으로 먼저 변환 (변환 불가한 값은 NaN 처리)
df_signal['X좌표'] = pd.to_numeric(df_signal['X좌표'], errors='coerce')
df_signal['Y좌표'] = pd.to_numeric(df_signal['Y좌표'], errors='coerce')

# 좌표 변환기: TM → WGS84
print("🧭 좌표 변환 시작")
print(df_signal['X좌표'].describe())
print(df_signal['Y좌표'].describe())
print(df_signal['X좌표'].apply(lambda x: isinstance(x, float)).value_counts())
time.sleep(1)
transformer = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)


print("✅ 숫자형 변환 후 요약:")
print(df_signal[['X좌표', 'Y좌표']].describe())

# 유효한 좌표에 대해서만 변환
mask = df_signal['X좌표'].notna() & df_signal['Y좌표'].notna()
print(f"🧮 유효 좌표 수: {mask.sum()} / {len(df_signal)}")
df_signal.loc[mask, ['위도', '경도']] = df_signal.loc[mask].apply(
    lambda row: pd.Series(transformer.transform(row['X좌표'], row['Y좌표'])),
    axis=1
)

# 최종 출력용 데이터 정리
df_signal = df_signal[['순번', '자치구', '횡단보도종류', '경도', '위도', '주소']]
df_signal.rename(columns={'순번': '연번', '횡단보도종류': '신호등종류'}, inplace=True)
df_signal.rename(columns={'경도': 'X좌표', '위도': 'Y좌표'}, inplace=True)

# 데이터 확인 출력
print(df_signal.head())
print(df_signal.columns) 
print(df_signal.info())


# 지도 중심 좌표 (서울시청 기준)
print("🗺️ 지도 생성 중...")
time.sleep(3)
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
# 신호등 위치 마커 추가
valid_rows = df_signal[df_signal['Y좌표'].notna() & df_signal['X좌표'].notna()]
print(f"✅ 시각화 가능한 신호등 수: {len(valid_rows)}개")
for _, row in valid_rows.iterrows():
    folium.CircleMarker(
        location=[row['Y좌표'], row['X좌표']],
        radius=1,
        color='red',
        fill=True,
        fill_opacity=0.7
    ).add_to(m)
# 지도 저장
m.save("signal_map_seoul.html")
print("✅ 지도 저장 완료: signal_map_seoul.html")
time.sleep(1)