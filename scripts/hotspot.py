import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon

# 공통 로직 함수: 사고 -> 그리드 격자 + 사고다발지역 추출
def _generate_hotspots(df_filtered, grid_size, min_accidents):
    gdf = gpd.GeoDataFrame(
        df_filtered,
        geometry=gpd.points_from_xy(df_filtered["lng"], df_filtered["lat"]),
        crs="EPSG:4326"
    ).to_crs(epsg=5186)

    minx, miny, maxx, maxy = gdf.total_bounds
    grid_cells = [
        Polygon([(x, y), (x + grid_size, y), (x + grid_size, y + grid_size), (x, y + grid_size)])
        for x in np.arange(minx, maxx, grid_size)
        for y in np.arange(miny, maxy, grid_size)
    ]
    grid = gpd.GeoDataFrame({'geometry': grid_cells}, crs=gdf.crs)

    joined = gpd.sjoin(gdf, grid, how='left', predicate='within')
    counts = joined.groupby("index_right").size()

    hotspot_index = counts[counts >= min_accidents].index
    hotspot_grid = grid.loc[hotspot_index].copy()
    hotspot_grid["accident_count"] = counts[hotspot_index].values
    hotspot_grid["center_x"] = hotspot_grid.geometry.centroid.x
    hotspot_grid["center_y"] = hotspot_grid.geometry.centroid.y

    return hotspot_grid

# 통합 실행 함수
def generate_combined_hotspot_file(input_path, output_csv_path,
                                   output_senior_summary, output_non_senior_summary):
    df = pd.read_csv(input_path)

    # 고령자 필터링 및 다발지역 계산
    df_senior = df[df["acdnt_age_1_code"] >= 65].copy()
    senior_hotspot_grid = _generate_hotspots(df_senior, grid_size=100, min_accidents=5)

    # 비고령자 필터링 및 다발지역 계산
    df_non_senior = df[df["acdnt_age_1_code"] < 65].copy()
    non_senior_hotspot_grid = _generate_hotspots(df_non_senior, grid_size=100, min_accidents=10)

    # 전체 사고 데이터 GDF
    all_gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lng"], df["lat"]),
        crs="EPSG:4326"
    ).to_crs(epsg=5186)

    # 고령자 사고다발 포함 여부
    senior_joined = gpd.sjoin(all_gdf, senior_hotspot_grid, how="left", predicate="within")
    all_gdf["senior_hotspot"] = senior_joined["index_right"].notnull().astype(int)

    # 비고령자 사고다발 포함 여부
    non_senior_joined = gpd.sjoin(all_gdf, non_senior_hotspot_grid, how="left", predicate="within")
    all_gdf["non_senior_hotspot"] = non_senior_joined["index_right"].notnull().astype(int)

    # 최종 CSV 저장
    all_gdf.drop(columns="geometry").to_csv(output_csv_path, index=False)
    print(f"[✔] 사고 데이터 저장 완료: {output_csv_path}")

    # 요약 파일 저장 (고령자)
    senior_summary = senior_hotspot_grid.set_geometry(senior_hotspot_grid.centroid).to_crs(epsg=4326)
    senior_summary["hotspot_center_lat"] = senior_summary.geometry.y
    senior_summary["hotspot_center_lng"] = senior_summary.geometry.x
    senior_summary[["hotspot_center_lat", "hotspot_center_lng", "accident_count"]] \
        .to_csv(output_senior_summary, index=False)
    print(f"[✔] 고령자 사고다발지역 저장 완료: {output_senior_summary}")

    # 요약 파일 저장 (비고령자)
    non_senior_summary = non_senior_hotspot_grid.set_geometry(non_senior_hotspot_grid.centroid).to_crs(epsg=4326)
    non_senior_summary["hotspot_center_lat"] = non_senior_summary.geometry.y
    non_senior_summary["hotspot_center_lng"] = non_senior_summary.geometry.x
    non_senior_summary[["hotspot_center_lat", "hotspot_center_lng", "accident_count"]] \
        .to_csv(output_non_senior_summary, index=False)
    print(f"[✔] 비고령자 사고다발지역 저장 완료: {output_non_senior_summary}")


# 실행부
if __name__ == "__main__":
    generate_combined_hotspot_file(
        input_path="./data/processed/accident_data_filtered.csv",
        output_csv_path="./data/processed/accident_with_hotspot.csv",
        output_senior_summary="./data/raw/hotspot_info_senior.csv",
        output_non_senior_summary="./data/raw/hotspot_info_non_senior.csv"
    )
