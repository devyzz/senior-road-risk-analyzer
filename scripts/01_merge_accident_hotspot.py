# ──────────────────────────────────────────────────────────────
# 교통사고 데이터 전처리 (고령/비고령 운전자 hotspot 클러스터링)
#
# - 대상: 2021~2023년 교통사고 데이터(Taas)
# - 목적: 고령운전자/비고령운전자 사고 데이터를 구분하여, 클러스터링 기반 사고다발지역 식별
# - 작업: 
#   - 연도별 사고 데이터 통합
#   - DBSCAN 클러스터링(위도/경도 기반, 반경 100m, 최소 5건(taas 고령운전자 기준))
#   - 각 사고에 다발지 여부 및 중심좌표 컬럼 추가 
#   - 연도별 저장
# ──────────────────────────────────────────────────────────────


import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN

# 연도별 데이터 통합
def load_and_concat_data(paths):
    dfs = [pd.read_csv(path) for path in paths]
    return pd.concat(dfs, ignore_index=True)

# DBSCAN + hotspot 여부 + 중심좌표 추가
def cluster_and_mark(df, lat_col='lat', lng_col='lng', eps_m=100, min_samples=5):
    coords = np.radians(df[[lat_col, lng_col]].values)
    db = DBSCAN(eps=eps_m / 6371000, min_samples=min_samples, metric='haversine').fit(coords)
    df['cluster'] = db.labels_
    df['is_hotspot'] = (df['cluster'] != -1).astype(int)

    # 중심좌표 계산
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

# 고령/비고령 운전자 분석 및 컬럼 추가
def assign_hotspot_columns(df_all, lat_col='lat', lon_col='lng', id_col='acdnt_no'):
    # 고령 운전자 기준: 100m, 5건 이상
    elderly = df_all[df_all['acdnt_age_1_code'] >= 65].copy()
    elderly = cluster_and_mark(elderly, lat_col, lon_col, eps_m=100, min_samples=5)
    elderly = elderly[[id_col, 'is_hotspot', 'hotspot_center_lat', 'hotspot_center_lng']]
    elderly.columns = [id_col, 'elderly_hotspot', 'elderly_hotspot_lat', 'elderly_hotspot_lng']

    # 비고령 운전자 기준: 100m, 7건 이상
    non_elderly = df_all[df_all['acdnt_age_1_code'] < 65].copy()
    non_elderly = cluster_and_mark(non_elderly, lat_col, lon_col, eps_m=100, min_samples=7)
    non_elderly = non_elderly[[id_col, 'is_hotspot', 'hotspot_center_lat', 'hotspot_center_lng']]
    non_elderly.columns = [id_col, 'non_elderly_hotspot', 'non_elderly_hotspot_lat', 'non_elderly_hotspot_lng']

    # 전체 운전자 기준: 50m, 5건 이상
    all_drivers = df_all.copy()
    all_drivers = cluster_and_mark(all_drivers, lat_col, lon_col, eps_m=50, min_samples=5)
    all_drivers = all_drivers[[id_col, 'is_hotspot', 'hotspot_center_lat', 'hotspot_center_lng']]
    all_drivers.columns = [id_col, 'all_hotspot', 'all_hotspot_lat', 'all_hotspot_lng']

    # 병합
    df_result = df_all.merge(elderly, on=id_col, how='left')
    df_result = df_result.merge(non_elderly, on=id_col, how='left')
    df_result = df_result.merge(all_drivers, on=id_col, how='left')

    return df_result

# 연도별 분할 저장
def split_by_year_and_save(df_result, year_col='acdnt_year'):
    for year, df_year in df_result.groupby(year_col):
        df_year.to_csv(f"./data/processed/accident_data_with_hotspot_{year}.csv", index=False)

# 실행
if __name__ == "__main__":
    paths = [
        "./data/raw/all_accident_info_2021.csv",
        "./data/raw/all_accident_info_2022.csv",
        "./data/raw/all_accident_info_2023.csv"
    ]
    df_all = load_and_concat_data(paths)
    df_result = assign_hotspot_columns(df_all, lat_col='lat', lon_col='lng', id_col='acdnt_no')
    split_by_year_and_save(df_result)
