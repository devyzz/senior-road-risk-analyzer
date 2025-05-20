# 외부 데이터 수집 
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import requests
import certifi
import pandas as pd
import xml.etree.ElementTree as ET

from pyproj import Transformer
from dotenv import load_dotenv

import utils.GEO_UTILS as GU
import utils.CONSTANTS as CONST

# 교차로 데이터 수집 (from csv)
def process_intersection():
    print("==>0. 교차로 데이터 처리 시작")
    file_path = "./data/raw/traffic_intersection.csv"
    df = pd.read_csv(file_path)
    
    df = df[["INTR_NM", "XCRD", "YCRD"]]

    df[["위도", "경도"]] = GU.convert_coordinates(df, "XCRD", "YCRD", "위도", "경도")
    
    df = df[["INTR_NM", "위도", "경도"]]
    
    output_path = "./data/external/intersection_data.csv"
    df.to_csv(output_path, index=False)
    print(f"===> 교차로 CSV 저장 완료: {output_path}")

# 횡단보도 데이터 수집 (from xlsx)
def process_crosswalk():
    print("==>1. 횡단보도 데이터 처리 시작")
    file_path = "./data/raw/서울특별시_자치구별 신호등 및 횡단보도 위치 및 현황_20230530.xlsx"
    df = pd.read_excel(file_path, engine='openpyxl', header=2)

    if df.columns[0].startswith("Unnamed"):
        df = df.drop(columns=[df.columns[0]])
        df.columns = ['순번', '자치구', '관리번호', '횡단보도종류', '주소', '교차로명', 'X좌표', 'Y좌표', '도로구분']
    
    df.reset_index(drop=True, inplace=True)
    df["X좌표"] = pd.to_numeric(df["X좌표"], errors="coerce")
    df["Y좌표"] = pd.to_numeric(df["Y좌표"], errors="coerce")
          
    df[["위도", "경도"]] = GU.convert_coordinates(df, "X좌표", "Y좌표", "위도", "경도")

    df["구분"] = "횡단보도"
    df = df[["구분", "위도", "경도"]]

    output_path = "./data/external/crosswalk_data.csv"
    df.to_csv(output_path, index=False)
    print(f"===> 횡단보도 CSV 저장 완료: {output_path}")

# 신호등 데이터 수집 (from csv)
def process_traffic_light():
    print("==>2. 신호등 데이터 처리 시작")
    file_path = "./data/raw/서울시 신호등 관련 정보.csv"
    df = pd.read_csv(file_path, encoding="euc-kr")

    df = df[["부착대관리번호", "신호등종류", "X좌표", "Y좌표"]]
    df = df[df["신호등종류"].isin([2.0, 3.0, 4.0, 5.0, 6.0, 21.0])]
    df = df.drop_duplicates(subset=["X좌표", "Y좌표"])
    df["X좌표"] = pd.to_numeric(df["X좌표"], errors="coerce")
    df["Y좌표"] = pd.to_numeric(df["Y좌표"], errors="coerce")
    

    df[["위도", "경도"]] = GU.convert_coordinates(df, "X좌표", "Y좌표", "위도", "경도")
    
    def classify_signal(x):
        if x in [2.0, 5.0]:
            return "3색등"
        elif x in [3.0, 6.0]:
            return "4색등"
        elif x in [4.0, 21.0]:
            return "2행등"
        else:
            return "기타"

    df["구분"] = df["신호등종류"].apply(classify_signal)    # 기타는 예외 처리용
    df = df[["구분", "위도", "경도"]]
    
    output_path = "./data/external/traffic_light_data.csv"
    df.to_csv(output_path, index=False)
    print(f"===> 신호등 CSV 저장 완료: {output_path}")

# 보호구역 데이터 수집 (from OpenAPI)
def process_protection_zone():
    print("==>3. 보호구역(OpenAPI) 데이터 처리 시작")

    # API 키 불러오기
    load_dotenv()
    api_key = os.getenv("UTIC_API_KEY")
    print(api_key)
    if not api_key:
        print("⚠️ API_KEY가 설정되지 않았습니다.")
        return
    
    # API 호출
    url = "http://www.utic.go.kr/guide/getSafeOpenJson.do"
    params = {
        "key": api_key,
        "type": "json",
        "sidoCd": CONST.SEOUL
    }
    response = requests.get(url, params=params, verify=certifi.where())

    if response.status_code != 200:
        print(f"⚠️ HTTP 오류 발생: {response.status_code}")
        return

    data = response.json()
    if data.get("resultCode") != "00":
        print(f"⚠️ API 요청 실패: {data.get('resultMsg')}")
        return

    # 데이터 가공
    extracted = []
    for item in data.get("items", []):
        code = str(item.get("FCLTY_TY"))
        x = item.get("X")
        y = item.get("Y")
        if code in CONST.ZONE_TYPE and x and y:
            extracted.append({
                "구분": CONST.ZONE_TYPE[code],
                "경도": x,
                "위도": y
            })

    df = pd.DataFrame(extracted)[["구분", "위도", "경도"]]

    output_path = "./data/external/protection_zone_data.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"===> 보호구역 CSV 저장 완료: {output_path}")
    
def process_traffic_spots():
    print("==>4. 교통량 지점 정보(OpenAPI) 데이터 처리 시작")

    load_dotenv()
    api_key = os.getenv("SEOUL_OPENAPI_KEY")
    if not api_key:
        print("⚠️ API_KEY가 설정되지 않았습니다.")
        return
    
    # API 요청
    url = f"http://openapi.seoul.go.kr:8088/{api_key}/xml/SpotInfo/1/1000/"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"⚠️ HTTP 오류 발생: {response.status_code}")
        return

    root = ET.fromstring(response.content)
    rows = root.findall("row")
    if not rows:
        print("⚠️ 응답 데이터에 <row> 항목이 없습니다.")
        return

    data = []
    for row in rows:
        try:
            data.append({
                "지점번호": row.findtext("spot_num"),
                "지점명": row.findtext("spot_nm"),
                "grs80tm_x": float(row.findtext("grs80tm_x")),
                "grs80tm_y": float(row.findtext("grs80tm_y")),
            })
        except Exception as e:
            print(f"⚠️ 일부 데이터 오류로 건너뜀: {e}")

    df = pd.DataFrame(data)
    
    df[["lat", "lng"]] = GU.convert_coordinates(df, "grs80tm_x", "grs80tm_y", "lat", "lng", epsg_from=5181, epsg_to=4326)
    # transformer = Transformer.from_crs("EPSG:5181", "EPSG:4326", always_xy=True)
    # df[["lng", "lat"]] = df.apply(
    #     lambda row: pd.Series(transformer.transform(row["grs80tm_x"], row["grs80tm_y"])),
    #     axis=1
    # )
    df.drop(columns=["grs80tm_x", "grs80tm_y"], inplace=True)

    #저장
    output_path = "./data/external/traffic_spot_data.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df[["지점번호", "지점명", "lat", "lng"]].to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"===> 교통량 지점 CSV 저장 완료: {output_path}")
    
def merge_traffic_data() -> pd.DataFrame:
    traffic_df = pd.read_csv("./data/raw/traffic_spot_info.csv")
    spot_df = pd.read_csv("./data/external/traffic_spot_data.csv").drop(columns=["지점명"], errors="ignore")
    traffic_df = pd.concat([traffic_df.reset_index(drop=True), spot_df.reset_index(drop=True)], axis=1)
    traffic_df.to_csv("./data/raw/traffic_mereg_data.csv", index=False, encoding="utf-8-sig")
    print("✅ 최종 병합 저장 완료: ./data/raw/traffic_merge_data.csv")


if __name__ == "__main__":
    # process_crosswalk()
    process_intersection()
    # process_traffic_light()
    # process_protection_zone()
    # process_traffic_spots()
    # merge_traffic_data()
