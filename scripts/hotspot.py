import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon

def generate_hotspot_flags(
    input_path: str,
    output_path: str,
    age_cut: int = 65,
    grid_size: int = 100,
    min_accidents: int = 5
):
    # 1. 사고 데이터 로드
    df = pd.read_csv(input_path)
    
    # 2. 고령운전자 필터링 (age_cut 이상)
    df_filtered = df[df['acdnt_age_1_code'] >= age_cut].copy()

    # 3. GeoDataFrame 변환 (위도, 경도 -> geometry)
    gdf = gpd.GeoDataFrame(
        df_filtered,
        geometry=gpd.points_from_xy(df_filtered['lng'], df_filtered['lat']),
        crs="EPSG:4326"
    ).to_crs(epsg=5186)  # 서울 기준 거리 계산을 위해 TM 좌표계로 변환

    # 4. 100m 그리드 생성
    minx, miny, maxx, maxy = gdf.total_bounds
    grid_cells = []
    for x in np.arange(minx, maxx, grid_size):
        for y in np.arange(miny, maxy, grid_size):
            cell = Polygon([
                (x, y), (x + grid_size, y),
                (x + grid_size, y + grid_size), (x, y + grid_size)
            ])
            grid_cells.append(cell)

    grid = gpd.GeoDataFrame({'geometry': grid_cells}, crs=gdf.crs)

    # 5. 그리드에 사고 수 계산
    joined = gpd.sjoin(gdf, grid, how='left', predicate='within')
    counts = joined.groupby("index_right").size()
    hotspot_index = counts[counts >= min_accidents].index
    hotspot_grid = grid.loc[hotspot_index]

    # 6. 전체 사고데이터로 다시 in_hotspot 플래그 지정
    all_gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lng"], df["lat"]),
        crs="EPSG:4326"
    ).to_crs(epsg=5186)

    all_gdf["in_hotspot"] = all_gdf.geometry.apply(
        lambda pt: int(hotspot_grid.contains(pt).any())
    )

    # 7. 결과 저장
    all_gdf.to_crs(epsg=4326).drop(columns='geometry').to_csv(output_path, index=False)
    print(f"[✔] 결과 저장 완료: {output_path}")

# ------------------------------
# 예시 실행
if __name__ == "__main__":
    generate_hotspot_flags(
        input_path='./data/processed/accident_data_filtered.csv',
        output_path='./data/processed/accident_with_hotspot.csv',
        age_cut=65,
        grid_size=100,
        min_accidents=5
    )