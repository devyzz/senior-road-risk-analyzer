import requests
import xml.etree.ElementTree as ET
import pandas as pd
import time
import os
from dotenv import load_dotenv

def fetch_seoul_traffic_intersections(
    api_key: str,
    total_rows: int = 9000,
    rows_per_page: int = 1000,
    output_file: str = "./data/raw/traffic_intersection.csv"
):
    base_url = "http://openapi.seoul.go.kr:8088"
    service_name = "trafficSafetyA008PInfo"
    request_type = "xml"

    target_columns = [
        'INTR_CD', 'INTR_NM', 'TYPE_CD', 'GU_CD',
        'LOTNO', 'ROAD_SE', 'INTR_MNG_NO', 'SPC_DATA',
        'APT_DONG_CODE', 'XCRD', 'YCRD'
    ]

    all_data = []
    start_time = time.time()

    for start in range(1, total_rows + 1, rows_per_page):
        end = min(start + rows_per_page - 1, total_rows)
        url = f"{base_url}/{api_key}/{request_type}/{service_name}/{start}/{end}"
        response = requests.get(url)
        root = ET.fromstring(response.content)
        rows = root.findall(".//row")

        for row in rows:
            row_data = {col: row.findtext(col) for col in target_columns}
            all_data.append(row_data)

        elapsed = time.time() - start_time
        print(f"{start} ~ {end}행 수집 완료 | 누적 시간: {elapsed:.2f}초")

    # 결과 저장
    df = pd.DataFrame(all_data)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    total_elapsed = time.time() - start_time
    print(f"전체 수집 완료! 총 {len(df)}개")
    print(f"저장 위치: {output_file}")


# ----------------------------
# 직접 실행할 경우
if __name__ == "__main__":
    load_dotenv()  # .env 파일 로드
    api_key = os.getenv("SEOUL_OPENAPI_KEY")

    if not api_key:
        raise ValueError("환경변수 'SEOUL_API_KEY'를 .env에 설정해주세요.")

    fetch_seoul_traffic_intersections(
        api_key=api_key,
        total_rows=8486,
        rows_per_page=1000,
        output_file="./data/raw/traffic_intersection.csv"
    )