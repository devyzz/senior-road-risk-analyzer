'''
도로교통공단 교통사고 정보 (TAAS) 데이터 크롤링
'''
import os
import time
import json
import pandas as pd
from pyproj import Transformer

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

# 설정 
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")  # 디버깅 시 주석처리 가능
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 필터 설정
def apply_conditions(driver, year, sigungu):
    
    driver.find_element(By.ID, "menuPartSearch").click()
    time.sleep(1)
    
    # 연도 및 지역
    Select(driver.find_element(By.ID, "ptsRafYearStart")).select_by_visible_text(year)
    time.sleep(1)
    Select(driver.find_element(By.ID, "ptsRafYearEnd")).select_by_visible_text(year)
    time.sleep(1)
    Select(driver.find_element(By.ID, "ptsRafSido")).select_by_visible_text("서울특별시")
    time.sleep(1)
    Select(driver.find_element(By.ID, "ptsRafSigungu")).select_by_visible_text(sigungu)
    time.sleep(1)

    # 체크박스 필터 (사망, 중상, 경상 사고)
    values_to_check = ["01", "02", "03", "04"]
    for value in values_to_check:
        checkbox = driver.find_element(By.CSS_SELECTOR, f'input[name="ACDNT_GAE_CODE"][value="{value}"]')
        if not checkbox.is_selected():
            checkbox.click()
    time.sleep(2)
    
    # 단순조건: 노인 운전자 사고
    # Select(driver.find_element(By.ID, "ptsRafSimpleCondition")).select_by_visible_text("노인 운전자 사고")
    # time.sleep(1)
    
    driver.find_element(By.CLASS_NAME, "btn-search").click()
    time.sleep(7)

# 사고 데이터 추출
def extract_accident_data(driver):
    logs = driver.get_log("performance")
    for entry in logs:
        message = json.loads(entry["message"])["message"]
        if (
            message["method"] == "Network.responseReceived"
            and "selectAccidentInfo.do" in message.get("params", {}).get("response", {}).get("url", "")
        ):
            request_id = message["params"]["requestId"]
            resp_body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
            return json.loads(resp_body["body"])["resultValue"]["accidentInfoList"]
    raise Exception("❌ 사고 데이터 응답을 찾을 수 없습니다.")

# 좌표 변환
def convert_coordinates(row, transformer):
    try:
        lng, lat = transformer.transform(row["x_crdnt"], row["y_crdnt"])
        return pd.Series({"lat": lat, "lng": lng})
    except:
        return pd.Series({"lat": None, "lng": None})

def main():
    sigungu_list = [
        "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구", "동대문구", "동작구",
        "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "용산구", "영등포구", "은평구", "종로구", "중랑구", "중구"
    ]
    year_list = ["2021", "2022", "2023"]
    all_data = []

    for year in year_list:
        driver = setup_driver()
        try:
            driver.get("https://taas.koroad.or.kr/gis/mcm/mcl/initMap.do?menuId=GIS_GMP_STS_RSN")
            time.sleep(2)

            for sigungu in sigungu_list:
                print(f"==={year}년 {sigungu} 데이터 수집 중===")
                try:
                    apply_conditions(driver, year, sigungu)
                    accidents = extract_accident_data(driver)

                    # ✅ 연도 및 시군구 정보 추가
                    for accident in accidents:
                        accident["year"] = year
                        accident["sigungu"] = sigungu

                except Exception as e:
                    print(f"❌ {year}년 {sigungu} 데이터 수집 실패: {e}")
                    accidents = []
                all_data.extend(accidents)

        finally:
            driver.quit()

    # DataFrame 변환 및 좌표 처리
    df = pd.DataFrame(all_data)
    if df.empty:
        print("❗데이터가 없습니다.")
        return

    transformer = Transformer.from_crs("epsg:5179", "epsg:4326", always_xy=True)
    df[["lat", "lng"]] = df.apply(lambda row: convert_coordinates(row, transformer), axis=1)
    
    # 저장 경로 설정 및 디렉토리 생성
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "accident_info_list.csv")

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ 총 {len(df)}건의 사고 데이터 저장 : {output_path}")


if __name__ == "__main__":
    main()
