# TAAS 교통사고 데이터 수집 (Selenium 크롤링)
# 대상: 서울시 교통사고 정보 (좌표 포함)

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

import scripts.utils.CONSTANTS as CONST
import scripts.utils.GEO_UTILS as GU

def get_accident_df(year_list=CONST.TAAS_YEARS, sigungu_list=CONST.SEOUL_DISTRICTS):
    
    all_data = []

    for year in year_list:
        driver = _setup_driver()
        try:
            driver.get("https://taas.koroad.or.kr/gis/mcm/mcl/initMap.do?menuId=GIS_GMP_STS_RSN")
            time.sleep(2)

            for sigungu in sigungu_list:
                print(f"==={year}년 {sigungu} 데이터 수집 중===")
                try:
                    _apply_conditions(driver, year, sigungu)
                    accidents = _extract_accident_data(driver)

                    for accident in accidents:
                        accident["year"] = year
                        accident["sigungu"] = sigungu

                    all_data.extend(accidents)

                except Exception as e:
                    print(f"❌ {year}년 {sigungu} 데이터 수집 실패: {e}")

        finally:
            driver.quit()

    df = pd.DataFrame(all_data)
    df[["lat", "lng"]] = GU.convert_coordinates(df, "x_crdnt", "y_crdnt", "lat", "lng", epsg_from=5179, epsg_to=4326)
        
    if df.empty:
        print("==>데이터가 없습니다.")
        return pd.DataFrame()

    print(f"✅ 총 {len(df)}건의 사고 데이터 수집 완료")
    return df


# ────────────── 내부 함수 ──────────────

def _setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def _apply_conditions(driver, year, sigungu):
    driver.find_element(By.ID, "menuPartSearch").click()
    time.sleep(1)

    Select(driver.find_element(By.ID, "ptsRafYearStart")).select_by_visible_text(year)
    Select(driver.find_element(By.ID, "ptsRafYearEnd")).select_by_visible_text(year)
    Select(driver.find_element(By.ID, "ptsRafSido")).select_by_visible_text("서울특별시")
    Select(driver.find_element(By.ID, "ptsRafSigungu")).select_by_visible_text(sigungu)

    time.sleep(1)

    for value in ["01", "02", "03", "04"]:
        checkbox = driver.find_element(By.CSS_SELECTOR, f'input[name="ACDNT_GAE_CODE"][value="{value}"]')
        if not checkbox.is_selected():
            checkbox.click()

    time.sleep(1)
    driver.find_element(By.CLASS_NAME, "btn-search").click()
    time.sleep(7)


def _extract_accident_data(driver):
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


# ────────────── 테스트 실행 ──────────────

if __name__ == "__main__":
    df = get_accident_df()
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/accident_info_list.csv", index=False, encoding="utf-8-sig")
    print("✅ accident_info_list.csv 저장 완료")
