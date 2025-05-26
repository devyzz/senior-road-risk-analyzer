import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.neighbors import BallTree
import geopandas as gpd

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import utils.GEO_UTILS as GU
import utils.CONSTANTS as CONST

# === 교통량 병합 ===
def process_traffic_volume(accident_df: pd.DataFrame, year: int) -> pd.DataFrame:
    traffic_df = pd.read_csv("./data/raw/traffic_mereg_data.csv")
    print(f"=> {year}년 사고 + 교통량 병합 중...")

    traffic_coords = traffic_df[["lat", "lng", "2021", "2022", "2023"]].copy()
    tree = BallTree(np.radians(traffic_coords[["lat", "lng"]].values), metric='haversine')

    acc_coords = accident_df[["lat", "lng"]].values
    acc_years = accident_df["acdnt_year"].astype(str).values
    distances, indices = tree.query(np.radians(acc_coords), k=1)

    traffic_values = []
    for i, dist_km in enumerate(distances.flatten() * 6371):
        if dist_km > 2.0:
            traffic_values.append(np.nan)
            continue

        nearest = traffic_coords.iloc[indices[i]]

        # // Changed ✅: 단일 값으로 안전하게 추출
        val = nearest[acc_years[i]]
        if isinstance(val, pd.Series):
            val = val.iloc[0]

        if pd.isna(val):
            fallback = [y for y in ["2021", "2022", "2023"] if y != acc_years[i]]
            val = pd.to_numeric(nearest[fallback].values.flatten(), errors='coerce').mean()

        traffic_values.append(val)

    accident_df["traffic_volume"] = traffic_values
    return accident_df


# === 속도/차로수 병합 ===
def enrich_velocity(accident_df: pd.DataFrame, year: int) -> pd.DataFrame:
    def refine(df):
        df = df[df["도로명"].notna() & (df["도로명"].str.strip() != "")]
        df["도로명"] = df["도로명"].str.replace(" ", "").str.strip()

        def parse_lanes(val):
            try:
                nums = list(map(int, str(val).strip().split("~")))
                return round(sum(nums) / len(nums))
            except:
                return np.nan

        df["차로수"] = df["차로수"].apply(parse_lanes)
        return df

    def pick_velocity(row):
        code = row["occrrnc_time_code"]
        return (
            row["오전"] if 6 < code < 10 else
            row["낮"] if 11 < code < 14 else
            row["오후"] if 16 < code < 20 else
            row["전일"]
        )

    velocity_df = refine(pd.read_csv(f"./data/raw/{year}velocity.csv"))
    merged = pd.merge(accident_df, velocity_df, how="inner", left_on="route_nm", right_on="도로명")
    merged["lanes"] = merged["차로수"]
    merged["lengths"] = pd.to_numeric(merged["연장"].str.replace(",", ""), errors="coerce")
    merged["velocity"] = merged.apply(pick_velocity, axis=1)

    return pd.merge(
        accident_df,
        merged[["acdnt_no", "lanes", "lengths", "velocity"]],
        how="left", on="acdnt_no"
    )


# === 연도별 처리 ===
def run_all_processing_steps(year: int = None):
    years = [2021, 2022, 2023] if year is None else [year]

    for y in years:
        print(f"==> {y}년 데이터 통합 처리 시작...\n")
        accident_df = pd.read_csv(f"./data/raw/all_accident_info_{y}.csv")

        # 보행환경 요소 병합
        for label, path, col_name, r, b in [
            ("crosswalk", "crosswalk_data.csv", "near_crosswalk", 15, 10),
            ("traffic_light", "traffic_light_data.csv", "near_traffic_light", 50, 25),
        ]:
            zone_df = pd.read_csv(f"./data/external/{path}")
            accident_df = GU.mark_zone_proximity_common(
                accident_df, zone_df,
                zone_lat_col="위도", zone_lng_col="경도",
                output_col=col_name, radius_m=r, buffer_m=b
            )

        zone_df = pd.read_csv("./data/external/protection_zone_data.csv")
        for zone_type, col_name in CONST.ZONE_COLUMNS.items():
            sub_df = zone_df[zone_df["구분"] == zone_type]
            accident_df = GU.mark_zone_proximity_common(
                accident_df, sub_df,
                zone_lat_col="위도", zone_lng_col="경도",
                output_col=col_name, radius_m=300, buffer_m=100
            )

        accident_df = enrich_velocity(accident_df, y)
        accident_df = process_traffic_volume(accident_df, y)
        accident_df.to_csv(f"./data/processed/accident_data_{y}.csv", index=False, encoding="utf-8-sig")
        print(f"====> 최종 저장 완료: ./data/processed/accident_data_{y}.csv\n")



# === 병합 ===
def merge_and_filter_all_years():
    print("===> 연도별 CSV 전체 병합 중...")
    files = [f"./data/processed/accident_data_{y}.csv" for y in range(2021, 2024)]
    dfs = [pd.read_csv(f, low_memory=False) for f in files]
    merged_df = pd.concat(dfs, ignore_index=True)

    merged_df = merged_df[~merged_df["wrngdo_vhcle_asort_dc"].isin(["자전거", "개인형이동수단(PM)"])]   # 사고유형에서 자전거 사고 제외
    
    # 필터링 단계
    columns_to_keep = [
        "acdnt_year", "occrrnc_time_code", "legaldong_name", "acdnt_hdc",
        "lrg_violt_1_dc", "road_stle_dc", "wrngdo_vhcle_asort_dc", "acdnt_age_1_code",
        "rdse_sttus_dc", "road_div", "lat", "lng",
        "near_crosswalk", "near_traffic_light", "near_child_zone",
        "near_elderly_zone", "near_disabled_zone",
        "lanes", "lengths", "velocity", "traffic_volume",
        "elderly_hotspot", "non_elderly_hotspot", "all_hotspot"
    ]
    filtered_df = merged_df[[col for col in columns_to_keep if col in merged_df.columns]]
    return filtered_df

# === 사고다발지 포함여부 병합 ===
def generate_hotspot(df):
    print("===> 사고다발지 병합 중...")
    df_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lng"], df["lat"]), crs="EPSG:4326").to_crs(epsg=5186)

    # 고령자 사고다발지역
    df_senior = df[df["acdnt_age_1_code"] >= 65].copy()
    senior_hotspot_grid = GU.generate_hotspots(df_senior, grid_size=100, min_accidents=5)
    senior_joined = gpd.sjoin(df_gdf, senior_hotspot_grid, how="left", predicate="within")
    df_gdf["elderly_hotspot"] = senior_joined["index_right"].notnull().astype(int)

    # 비고령자 사고다발지역
    df_non_senior = df[df["acdnt_age_1_code"] < 65].copy()
    non_senior_hotspot_grid = GU.generate_hotspots(df_non_senior, grid_size=100, min_accidents=10)
    non_senior_joined = gpd.sjoin(df_gdf, non_senior_hotspot_grid, how="left", predicate="within")
    df_gdf["non_elderly_hotspot"] = non_senior_joined["index_right"].notnull().astype(int)

    # 전체 핫스팟 여부 (둘 중 하나라도 해당되면 1)
    df_gdf["all_hotspot"] = ((df_gdf["elderly_hotspot"] == 1) | (df_gdf["non_elderly_hotspot"] == 1)).astype(int)
    df_gdf.drop(columns="geometry").to_csv("./data/processed/processed_accident_data.csv", index=False)
    
    # 고령자 필터링 및 다발지역 계산
    df_senior = df[df["acdnt_age_1_code"] >= 65].copy()
    senior_hotspot_grid = GU.generate_hotspots(df_senior, grid_size=100, min_accidents=5)

    # 비고령자 필터링 및 다발지역 계산
    df_non_senior = df[df["acdnt_age_1_code"] < 65].copy()
    non_senior_hotspot_grid = GU.generate_hotspots(df_non_senior, grid_size=100, min_accidents=10)
    
    output_senior_summary="./data/raw/hotspot_info_senior.csv"
    output_non_senior_summary="./data/raw/hotspot_info_non_senior.csv"
    
    # 요약 파일 저장 (고령자)
    senior_summary = senior_hotspot_grid.set_geometry(senior_hotspot_grid.centroid).to_crs(epsg=4326)
    senior_summary["hotspot_center_lat"] = senior_summary.geometry.y
    senior_summary["hotspot_center_lng"] = senior_summary.geometry.x
    senior_summary[["hotspot_center_lat", "hotspot_center_lng", "accident_count"]].to_csv(output_senior_summary, index=False)
    print(f"[✔] 고령자 사고다발지역 저장 완료: {output_senior_summary}")

    # 요약 파일 저장 (비고령자)
    non_senior_summary = non_senior_hotspot_grid.set_geometry(non_senior_hotspot_grid.centroid).to_crs(epsg=4326)
    non_senior_summary["hotspot_center_lat"] = non_senior_summary.geometry.y
    non_senior_summary["hotspot_center_lng"] = non_senior_summary.geometry.x
    non_senior_summary[["hotspot_center_lat", "hotspot_center_lng", "accident_count"]].to_csv(output_non_senior_summary, index=False)
    print(f"[✔] 비고령자 사고다발지역 저장 완료: {output_non_senior_summary}")

    
if __name__ == "__main__":
    # run_all_processing_steps()              #1. 전체 연도 병합 처리
    df = merge_and_filter_all_years()       #2. 데이터통합 및 필터링
    generate_hotspot(df)                    #3. 사고다발지 컬럼 추가 및 사고다발지 csv생성

