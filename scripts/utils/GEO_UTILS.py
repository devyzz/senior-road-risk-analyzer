import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import KDTree
from sklearn.cluster import DBSCAN
from math import radians, cos, sin, sqrt, atan2

# 지구 반지름 (단위: m)
EARTH_RADIUS_M = 6371000

# EPSG 기반 좌표계 변환 함수
def convert_coordinates(df, x_col, y_col, lat_col, lng_col, epsg_from=5186, epsg_to=4326):
    transformer = Transformer.from_crs(f"epsg:{epsg_from}", f"epsg:{epsg_to}", always_xy=True)
    def transform_row(row):
        try:
            lng, lat = transformer.transform(row[x_col], row[y_col])
            return pd.Series({lat_col: lat, lng_col: lng})
        except:
            return pd.Series({lat_col: None, lng_col: None})
    return df.apply(transform_row, axis=1)

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

# 교차로 근접성 마킹 함수
# accident_df: 사고 데이터프레임
# zone_df: 보호구역 데이터프레임
# accident_lat_col: 사고 데이터프레임의 위도 컬럼명
def mark_zone_proximity_common(
    accident_df, zone_df,
    accident_lat_col="lat", accident_lng_col="lng",
    zone_lat_col="Y", zone_lng_col="X",
    output_col="zone_flag",
    radius_m=300, buffer_m=100
):
    accident_df[output_col] = 0

    zone_df = zone_df.dropna(subset=[zone_lat_col, zone_lng_col])
    zone_coords_deg = zone_df[[zone_lat_col, zone_lng_col]].values
    zone_coords_rad = latlng_to_radians(zone_df, zone_lat_col, zone_lng_col)

    accident_coords_deg = accident_df[[accident_lat_col, accident_lng_col]].values
    accident_coords_rad = latlng_to_radians(accident_df, accident_lat_col, accident_lng_col)

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
    print(f"↘︎ [{output_col}] 컬럼 병합 완료 (총 {len(flags)}건)\n")  
    accident_df[output_col] = flags
    return accident_df



# DBSCAN + hotspot 여부 + 중심좌표 추가
def cluster_and_mark(df, lat_col='lat', lng_col='lng', eps_m=100, min_samples=5):
    coords = np.radians(df[[lat_col, lng_col]].values)
    db = DBSCAN(eps=eps_m / 6371000, min_samples=min_samples, metric='haversine').fit(coords)
    df['cluster'] = db.labels_
    df['is_hotspot'] = (df['cluster'] != -1).astype(int)

    centers = (
        df[df['is_hotspot'] == 1]
        .groupby('cluster')[[lat_col, lng_col]]
        .mean()
        .rename(columns={
            lat_col: 'hotspot_center_lat',
            lng_col: 'hotspot_center_lng'
        })
        .reset_index()
    )
    df = df.merge(centers, on='cluster', how='left')
    return df

# 고령/비고령/전체 기준 hotspot 분석 및 병합
def assign_hotspot_columns(df_all, lat_col='lat', lon_col='lng', id_col='acdnt_no'):
    print("====> Hotspot 분석 중...")

    elderly = df_all[df_all['acdnt_age_1_code'] >= 65].copy()
    elderly = cluster_and_mark(elderly, lat_col, lon_col, eps_m=100, min_samples=5)
    elderly = elderly[[id_col, 'is_hotspot', 'hotspot_center_lat', 'hotspot_center_lng']]
    elderly.columns = [id_col, 'elderly_hotspot', 'elderly_hotspot_lat', 'elderly_hotspot_lng']

    non_elderly = df_all[df_all['acdnt_age_1_code'] < 65].copy()
    non_elderly = cluster_and_mark(non_elderly, lat_col, lon_col, eps_m=100, min_samples=7)
    non_elderly = non_elderly[[id_col, 'is_hotspot', 'hotspot_center_lat', 'hotspot_center_lng']]
    non_elderly.columns = [id_col, 'non_elderly_hotspot', 'non_elderly_hotspot_lat', 'non_elderly_hotspot_lng']

    all_drivers = df_all.copy()
    all_drivers = cluster_and_mark(all_drivers, lat_col, lon_col, eps_m=50, min_samples=5)
    all_drivers = all_drivers[[id_col, 'is_hotspot', 'hotspot_center_lat', 'hotspot_center_lng']]
    all_drivers.columns = [id_col, 'all_hotspot', 'all_hotspot_lat', 'all_hotspot_lng']

    # 병합하여 df_all에 직접 추가
    df_all = df_all.merge(elderly, on=id_col, how='left')
    df_all = df_all.merge(non_elderly, on=id_col, how='left')
    df_all = df_all.merge(all_drivers, on=id_col, how='left')

    # 저장
    df_all.to_csv("./data/processed/accident_data_all.csv", index=False, encoding="utf-8-sig")
    print(f"====> hotspot 컬럼 포함 저장 완료")