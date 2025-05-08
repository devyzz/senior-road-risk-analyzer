# ──────────────────────────────────────────────────────────────
# 공공데이터포털 교통량 지점 정보(OpenAPI) 데이터 수집
# - 저장: CSV 파일 (UTF-8-sig)
# - 필요: API Key
# ──────────────────────────────────────────────────────────────

import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from pyproj import Transformer
from dotenv import load_dotenv

def fetch_traffic_spot_data(api_key: str, start_index=1, end_index=1000) -> pd.DataFrame:
    url = f"http://openapi.seoul.go.kr:8088/{api_key}/xml/SpotInfo/{start_index}/{end_index}/"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"API 요청 실패: {response.status_code}")
    
    root = ET.fromstring(response.content)
    rows = root.findall("row")
    if not rows:
        raise Exception("응답 데이터에서 <row> 항목이 없습니다.")

    data = []
    for row in rows:
        data.append({
            "지점번호": row.findtext("spot_num"),
            "지점명": row.findtext("spot_nm"),
            "grs80tm_x": float(row.findtext("grs80tm_x")),
            "grs80tm_y": float(row.findtext("grs80tm_y")),
        })

    return pd.DataFrame(data)

#좌표 -> 경도, 위도로 변경
def convert_grs80_to_wgs84(df: pd.DataFrame) -> pd.DataFrame:
    transformer = Transformer.from_crs("EPSG:5181", "EPSG:4326", always_xy=True)
    
    # 좌표 변환
    df[["lng", "lat"]] = df.apply(lambda row: pd.Series(transformer.transform(row["grs80tm_x"], row["grs80tm_y"])), axis=1)
    
    # 불필요한 원본 좌표 제거
    df.drop(columns=["grs80tm_x", "grs80tm_y"], inplace=True)
    
    return df

def save_to_csv(df: pd.DataFrame, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = df[["지점번호", "지점명", "lat", "lng"]]  
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"=> 저장 완료: {output_path}")

def main():
    load_dotenv()
    API_KEY = os.getenv("SEOUL_OPENAPI_KEY")
    if not API_KEY:
        raise ValueError("API_KEY가 .env에 설정되어 있지 않습니다. SEOUL_OPENAPI_KEY를 확인하세요.")
    
    print("=> 서울 교통량 측정지점 데이터 수집 시작")
    df = fetch_traffic_spot_data(API_KEY)
    df = convert_grs80_to_wgs84(df)
    save_to_csv(df, "./data/external/seoul_traffic_spots.csv")

if __name__ == "__main__":
    main()




