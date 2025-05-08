# ──────────────────────────────────────────────────────────────
# TAAS 교통사고 데이터 전처리 (정확도 향상을 위한 haversine 필터 추가)
#
# - 대상: 서울시 교통사고 정보(TAAS) + 횡단보도 위치 데이터
# - 작업: 사고지점 좌표를 기준으로 반경 10m 이내에
#        횡단보도 존재 여부를 판별하여, Boolean(1(True)/0(False)) 값으로 데이터 추가
#         ▶ near_crosswalk
# ──────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from scipy.spatial import KDTree
from math import radians, cos, sin, sqrt, atan2

# 지구 반지름 (단위: m)
EARTH_RADIUS_M = 6371000

# 위도/경도를 라디안으로 변환
def latlng_to_radians(df, lat_col="Y", lng_col="X"):   
    return np.radians(df[[lat_col, lng_col]].values)

# Haversine 거리계산
def haversine(lat1, lng1, lat2, lng2):
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return EARTH_RADIUS_M * c

def mark_zone_proximity(accident_df, crosswalk_df, radius_m=10, buffer_m =10):
    col_name = "near_crosswalk"
    accident_df[col_name] = 0
    
    crosswalk_df = crosswalk_df.dropna(subset=["위도", "경도"])
    zone_coords_deg = crosswalk_df[["위도", "경도"]].values
    zone_coords_rad = latlng_to_radians(crosswalk_df, "위도", "경도")

    accident_coords_deg = accident_df[["lat", "lng"]].values
    accident_coords_rad = latlng_to_radians(accident_df, "lat", "lng")
    
    tree = KDTree(zone_coords_rad)
    radius_rad = (radius_m + buffer_m) / EARTH_RADIUS_M
    candidates = tree.query_ball_point(accident_coords_rad, r=radius_rad)

    flags = []
    for i, match_idxs in enumerate(candidates):
        lat1, lng1 = accident_coords_deg[i]
        found = False
        for idx in match_idxs:
            lat2, lng2 = zone_coords_deg[idx]
            if haversine(lat1, lng1, lat2, lng2) <= radius_m:
                found = True
                break
        flags.append(1 if found else 0)

    accident_df[col_name] = flags
    return accident_df

# 연도별 처리 함수
def process_accident_year(year):
    print(f"=> {year}년 사고 데이터 처리 중...")

    crosswalk_path = "./data/external/crosswalk_2023_cleaned.csv"
    accident_path = f"./data/raw/all_accident_info_{year}.csv"
    output_path = f"./data/processed/accident_data_with_crosswalk_{year}.csv"

    accident_df = pd.read_csv(accident_path)
    crosswalk_df = pd.read_csv(crosswalk_path)

    accident_df = mark_zone_proximity(accident_df, crosswalk_df)

    accident_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"==> 저장 완료: {output_path}")

# 실행
if __name__ == "__main__":
    for year in range(2021, 2024):  # 2021~2023년 데이터 처리
        process_accident_year(year)
