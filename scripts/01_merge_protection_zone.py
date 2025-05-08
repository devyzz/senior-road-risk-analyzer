# ──────────────────────────────────────────────────────────────
# TAAS 교통사고 데이터 전처리 (정확도 향상을 위한 haversine 필터 추가)
#
# - 대상: 서울시 교통사고 정보(TAAS) + 보호구역 위치 데이터(UTIC)
# - 작업: 사고지점 좌표를 기준으로 반경 300m 이내에
#         보호구역(어린이/노인/장애인) 존재 여부를 판별하여,
#         다음 3개 컬럼을 Boolean(1(True)/0(False)) 값으로 추가
#         ▶ near_child_zone
#         ▶ near_elderly_zone
#         ▶ near_disabled_zone
# ──────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from scipy.spatial import KDTree
from math import radians, cos, sin, sqrt, atan2

# 보호구역 종류 매핑
ZONE_TYPES = ["어린이", "노인", "장애인"]
ZONE_COLUMNS = {
    "어린이": "near_child_zone",
    "노인": "near_elderly_zone",
    "장애인": "near_disabled_zone"
}

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

def mark_zone_proximity(accident_df, zone_df, zone_type, radius_m=300, buffer_m =100):
    col_name = ZONE_COLUMNS[zone_type]
    accident_df[col_name] = 0

    sub_zones = zone_df[zone_df["보호구역종류"] == zone_type].copy()
    if sub_zones.empty:
        return accident_df

    # 보호구역 좌표 추출 및 라디안변환
    zone_coords_deg = sub_zones[["Y", "X"]].values
    zone_coords_rad = latlng_to_radians(sub_zones, "Y", "X")

    # 사고지점 좌표 추출 및 라디안변환
    accident_coords_deg = accident_df[["lat", "lng"]].values
    accident_coords_rad = latlng_to_radians(accident_df, "lat", "lng")

    # KDTree로 후보군 빠르게 탐색
    # 라디안을 좌표를 변환하여 KDTree 모델로 계산하는 과정에서 지도상으로는 300m에 있는 보호구역임에도
    # 인덱스가 누락되는 경우가 발생. 따라서, KDTree로는 400m 반경 이내의 후보군을 찾고, 
    # 줄어든 후보군을 haversine 거리로 재검증하여 최종적으로 300m 이내의 보호구역을 찾는 식으로 코드를 수정함
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

    zone_path = "./data/external/protection_zone_data.csv"
    accident_path = f"./data/raw/all_accident_info_{year}.csv"
    output_path = f"./data/processed/accident_data_with_protectzones_{year}.csv"

    accident_df = pd.read_csv(accident_path)
    zone_df = pd.read_csv(zone_path)

    for ztype in ZONE_TYPES:
        accident_df = mark_zone_proximity(accident_df, zone_df, ztype)

    accident_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"==> 저장 완료: {output_path}")

# 실행
if __name__ == "__main__":
    for year in range(2021, 2024):  # 2021~2023년 데이터 처리
        process_accident_year(year)
