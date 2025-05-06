# ──────────────────────────────────────────────────────────────
# UTIC 보호구역(OpenAPI) 데이터 수집
#
# - 대상: 전국 어린이/노인/장애인 보호구역
# - 방식: 시도코드별 API 요청 (JSON 응답)
# - 저장: CSV 파일 (UTF-8-sig)
# - 필요: API Key 및 IP 등록
# ──────────────────────────────────────────────────────────────
from dotenv import load_dotenv
import requests
import pandas as pd
import os

# 보호구역 종류 매핑
ZONE_TYPE = {
    "1": "어린이",
    "2": "노인",
    "3": "장애인"
}

# 시도코드 단위 보호구역 데이터를 요청하여 리스트 반환
def fetch_protection_zone(api_key, sido_code) -> list:
    url = "https://www.utic.go.kr/guide/protZoneData.do"
    params = {
        "key": api_key,
        "type": "json",
        "sidoCd": sido_code,
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data.get("resultCode") == "00":
            return data.get("items", [])
        else:
            print(f"데이터 없음 또는 오류 (시도코드: {sido_code}) → {data.get('resultMsg')}")
    else:
        print(f"HTTP 오류 발생: {response.status_code}")
    return []

# 보호구역 리스트에서 보호구역 종류 + 좌표만 추출
def extract_coordinates(items: list) -> pd.DataFrame:
    extracted = []
    for item in items:
        code = str(item.get("FCLTY_TY"))
        x = item.get("X")
        y = item.get("Y")

        if code in ZONE_TYPE and x and y:
            extracted.append({
                "보호구역종류": ZONE_TYPE[code],
                "X": x,
                "Y": y
            })

    return pd.DataFrame(extracted)

# 전체 수집 → 필드 추출 → CSV 저장
def save_protection_zone_csv(api_key: str, output_path: str):
    sido_code = "11"  # 서울특별시
    print("=> 서울특별시 보호구역 데이터 수집 중...")
    items = fetch_protection_zone(api_key, sido_code)
    df = extract_coordinates(items)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"==> CSV 저장 완료: {output_path}")

if __name__ == "__main__":
    load_dotenv()
    API_KEY = os.getenv("UTIC_API_KEY")
    OUTPUT_PATH = "./data/external/protection_zone_data.csv"
    save_protection_zone_csv(API_KEY, OUTPUT_PATH)