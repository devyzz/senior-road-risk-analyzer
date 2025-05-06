# ──────────────────────────────────────────────────────────────
# TAAS 교통사고 데이터 전처리
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
from math import radians
import os

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

# KDTree 구축 (KDTree는 공간 검색을 위한 자료구조로, 반경 검색에 적합)
def build_kdtree(zone_df):              
    coords_rad = latlng_to_radians(zone_df, "Y", "X")
    return KDTree(coords_rad)

# 사고지점 반경 내 보호구역 존재 여부를 0/1로 표시
def mark_zone_proximity(accident_df, zone_df, zone_type, radius_m=300):
    col_name = ZONE_COLUMNS[zone_type]
    accident_df[col_name] = 0

    # 해당 종류만 필터링
    sub_zones = zone_df[zone_df["보호구역종류"] == zone_type].copy()
    if sub_zones.empty:
        return accident_df  # 해당 종류 없으면 바로 리턴

    # 라디안 좌표로 KDTree 구축
    tree = build_kdtree(sub_zones)

    # 사고지점도 라디안으로 변환
    accident_coords = latlng_to_radians(accident_df, "lat", "lng")

    # 반경(m) → 라디안 변환
    radius_rad = radius_m / EARTH_RADIUS_M

    # 사고지점마다 보호구역이 반경 내 존재하는지 확인
    result = tree.query_ball_point(accident_coords, r=radius_rad)

    # 인덱스 기준으로 Boolean 값 저장
    accident_df[col_name] = [1 if len(matches) > 0 else 0 for matches in result]
    return accident_df

def process_accident_year(year):
    print(f"=> {year}년 사고 데이터 처리 중...")
    
    # 파일 경로 설정
    zone_path = "./data/external/protection_zone_data.csv"
    accident_path = f"./data/processed/{year}_accident_data.csv"
    output_path = f"./data/processed/{year}_accident_with_zones.csv"

    # 데이터 로드
    accident_df = pd.read_csv(accident_path)
    zone_df = pd.read_csv(zone_path)

    # 보호구역 종류별 proximity 계산
    for ztype in ZONE_TYPES:
        accident_df = mark_zone_proximity(accident_df, zone_df, ztype)

    # 저장
    accident_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"==> 저장 완료: {output_path}")

if __name__ == "__main__":

    for year in range(2021, 2024):  # 2021 ~ 2023
        process_accident_year(year)