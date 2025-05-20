import sys
import os
import numpy as np
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from pathlib import Path
from sklearn.neighbors import BallTree
from sklearn.cluster import DBSCAN
import utils.GEO_UTILS as GU
import utils.CONSTANTS as CONST


def process_traffic_volume_combined(accident_df: pd.DataFrame, year: int) -> pd.DataFrame:
    traffic_df = pd.read_csv("./data/raw/traffic_mereg_data.csv")

    print(f"=> {year}년 사고 + 교통량 병합 중...")

    traffic_coords = traffic_df[["lat", "lng", "2021", "2022", "2023"]].copy()
    acc_coords = accident_df[["lat", "lng"]].values
    acc_years = accident_df["acdnt_year"].astype(str).values

    tree = BallTree(np.radians(traffic_coords[["lat", "lng"]].values), metric='haversine')
    distances, indices = tree.query(np.radians(acc_coords), k=1)

    distances_km = distances.flatten() * 6371
    indices = indices.flatten()

    traffic_values = []
    for i, dist in enumerate(distances_km):
        year_str = acc_years[i]
        if dist > 2.0:
            traffic_values.append(np.nan)
            continue

        nearest = traffic_coords.iloc[indices[i]]
        val = nearest[year_str]
        if pd.isna(val):
            fallback = [y for y in ["2021", "2022", "2023"] if y != year_str]
            val = pd.to_numeric(nearest[fallback], errors='coerce').mean()
        traffic_values.append(val)

    accident_df["traffic_volume"] = traffic_values
    return accident_df

def run_all_processing_steps(year):
    print(f"==> {year}년 데이터 통합 처리 시작...\n")

    accident_path = f"./data/raw/all_accident_info_{year}.csv"
    accident_df = pd.read_csv(accident_path)

    # 1. 횡단보도 존재유무 컬럼병합
    crosswalk_df = pd.read_csv("./data/external/crosswalk_data.csv")
    accident_df = GU.mark_zone_proximity_common(
        accident_df, crosswalk_df,
        zone_lat_col="위도", zone_lng_col="경도",
        output_col="near_crosswalk",
        radius_m=15, buffer_m=10
    )

    # 2. 신호등 존재유무 컬럼병합
    light_df = pd.read_csv("./data/external/traffic_light_data.csv")
    accident_df = GU.mark_zone_proximity_common(
        accident_df, light_df,
        zone_lat_col="위도", zone_lng_col="경도",
        output_col="near_traffic_light",
        radius_m=50, buffer_m=25
    )

    # 2. 보호구역 존재유무 컬럼 병합
    zone_df = pd.read_csv("./data/external/protection_zone_data.csv")
    for zone_type, col_name in CONST.ZONE_COLUMNS.items():
        sub_df = zone_df[zone_df["구분"] == zone_type]
        accident_df = GU.mark_zone_proximity_common(
            accident_df, sub_df,
            zone_lat_col="위도", zone_lng_col="경도",
            output_col=col_name,
            radius_m=300, buffer_m=100
        )

    # 3. 도로명, 차로수 컬럼 정제 / 속도 정보 추가
    def refine(df):
        df = df[df["도로명"].notna() & (df["도로명"].str.strip() != "")]
        df["도로명"] = df["도로명"].str.replace(" ", "").str.strip()
        
        def parse_lanes(val):
            try:
                parts = str(val).strip().split("~")
                nums = list(map(int, parts))
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
    merged_velocity = pd.merge(accident_df, velocity_df, how="inner", left_on="route_nm", right_on="도로명")
    merged_velocity["lanes"] = merged_velocity["차로수"]
    merged_velocity["lengths"] = pd.to_numeric(merged_velocity["연장"].str.replace(",", ""), errors="coerce")
    merged_velocity["velocity"] = merged_velocity.apply(pick_velocity, axis=1)
    accident_df = pd.merge(
        accident_df,
        merged_velocity[["acdnt_no", "lanes", "lengths", "velocity"]],
        how="left",
        on="acdnt_no"
    )
    
    # 4. 교통량
    accident_df = process_traffic_volume_combined(accident_df, year)

    # 저장
    output_path = f"./data/processed/accident_data_{year}.csv"
    accident_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"====> 최종 저장 완료: {output_path}\n")
    
def merge_all_years():
    print("===> 연도별 CSV 전체 병합 중...")
    base_dir = "./data/processed"
    file_names = [f"accident_data_{y}.csv" for y in range(2021, 2024)]
    
    # ⚠️ DtypeWarning 방지: low_memory=False 옵션 추가
    dfs = [pd.read_csv(os.path.join(base_dir, f), low_memory=False) for f in file_names]
    merged_df = pd.concat(dfs, ignore_index=True)
    
    before_rows = len(merged_df)
    remove_targets = ["자전거", "개인형이동수단(PM)"]
    merged_df = merged_df[~merged_df["wrngdo_vhcle_asort_dc"].isin(remove_targets)]
    after_rows = len(merged_df)
    print(f"🚲 '자전거' 운전자 행 제거됨: {before_rows - after_rows}건")
    
    merged_df.to_csv(os.path.join(base_dir, "accident_data_all.csv"), index=False, encoding="utf-8-sig")
    print("====> 병합 완료: accident_data_all.csv")    
    
    return merged_df
    
def filter_all_data():
    base_dir = "./data/processed"
    merged_file = os.path.join(base_dir, "accident_data_all.csv")

    if not Path(merged_file).exists():
        print(f"⚠️ 병합 파일이 존재하지 않습니다: {merged_file}")
        return

    df = pd.read_csv(merged_file, low_memory=False)

    # 필요한 컬럼만 선택
    columns_to_keep = [
        "acdnt_year", "occrrnc_time_code", "legaldong_name", "acdnt_hdc",
        "lrg_violt_1_dc", "road_stle_dc", "wrngdo_vhcle_asort_dc", "acdnt_age_1_code", #"acdnt_age_1_dc",
        "rdse_sttus_dc", "road_div", "lat", "lng",
        "near_crosswalk", "near_traffic_light", "near_child_zone",
        "near_elderly_zone", "near_disabled_zone",
        "lanes", "lengths", "velocity", "traffic_volume",
        "elderly_hotspot","non_elderly_hotspot","all_hotspot","route_nm"
    ]
    filtered_columns = [col for col in columns_to_keep if col in df.columns]
    filtered_df = df[filtered_columns]

    # 저장
    output_path = os.path.join(base_dir, "accident_data_filtered.csv")
    filtered_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"===> 필터링된 데이터 저장 완료: {output_path}")    

if __name__ == "__main__":
    #1. 연도별 사고 데이터 전처리 시작
    for year in [2021, 2022, 2023]:
        run_all_processing_steps(year)
    
    #2. 데이터통합 및 사고다발 구역 컬럼 추가
    all_df = merge_all_years()
    GU.assign_hotspot_columns(all_df, lat_col='lat', lon_col='lng', id_col='acdnt_no')
    
    #3. 데이터 필터링
    filter_all_data()
