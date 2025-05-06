# ──────────────────────────────────────────────────────────────
# TAAS 교통사고 데이터 전처리
#
# - 대상: TAAS 서울시 교통사고 + 서울시 교통정보 시스템 도로 속도 정보
# - 작업: 도로명 기준 병합 (평균속도, 차로수, 도로연장)
# ──────────────────────────────────────────────────────────────
import pandas as pd

#서울시 속도 정보 데이터 전처리 함수
def refine_velocity_dataset(input_path) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    df = df[df["도로명"].notna() & (df["도로명"].str.strip() != "")]
    df["도로명"] = df["도로명"].str.replace(" ", "").str.strip()
    return df

# 시간대 코드에 따른 속도컬럼 선택 함수
def select_avg_velocity(row) -> float:
    code = row["occrrnc_time_code"]
    if 6 < code < 10:
        return row["오전"]
    elif 11 < code < 14:
        return row["낮"]
    elif 16 < code < 20:
        return row["오후"]
    else:
        return row["전일"]
    
#사고 데이터에 도로속도/차로수/연장 병합 후 저장   
def merge_accident_with_velocity(accident_path, velocity_path, output_path) -> None:

    # 데이터 로드
    accident_df = pd.read_csv(accident_path)
    velocity_df = refine_velocity_dataset(velocity_path)

    # inner join
    merged_df = pd.merge(
        accident_df,
        velocity_df,
        how="inner",
        left_on="route_nm",
        right_on="도로명"
    )

    # 새로운 컬럼 생성
    merged_df["lanes"] = merged_df["차로수"]
    merged_df["lengths"] = pd.to_numeric(merged_df["연장"].str.replace(",", ""), errors="coerce")
    merged_df["velocity"] = merged_df.apply(select_avg_velocity, axis=1)

    # 필요한 컬럼만 추출 후 원본과 병합
    merged_info = merged_df[["acdnt_no", "lanes", "lengths", "velocity"]]
    accident_augmented_df = pd.merge(
        accident_df,
        merged_info,
        how="left",
        on="acdnt_no"
    )

    # 저장
    accident_augmented_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"==> 저장완료 : {output_path}")    

if __name__ == "__main__":
    for year in range(2021, 2024):  # 2021 ~ 2023
        print(f"=> {year}년 데이터 처리 중...")
        
        accident_path = f"./data/raw/all_accident_info_{year}.csv"
        velocity_path = f"./data/raw/{year}velocity.csv"  # 속도 데이터는 동일 사용
        output_path = f"./data/processed/{year}_accident_data.csv"

        merge_accident_with_velocity(
            accident_path=accident_path,
            velocity_path=velocity_path,
            output_path=output_path
        )
