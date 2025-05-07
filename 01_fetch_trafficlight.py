import pandas as pd
import requests
import folium
import time

# ✅ Kakao API Key
KAKAO_API_KEY = "KakaoAK fd5cd52e7afcde28a29cb81d157fb92e"

# ✅ 도로명 추출 함수
def get_road_name(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": KAKAO_API_KEY}
    params = {"x": lng, "y": lat}
    try:
        response = requests.get(url, headers=headers, params=params)
        time.sleep(1)  # 💡 과금 및 차단 방지
        if response.status_code == 200:
            documents = response.json().get('documents', [])
            if documents:
                road_address = documents[0].get('road_address')
                if road_address:
                    return road_address['road_name']
                else:
                    print(f"⚠️ 도로명 없음: 좌표=({lat}, {lng})")
            else:
                print(f"⚠️ documents 비어있음: 좌표=({lat}, {lng})")
        else:
            print(f"⚠️ 응답 실패: status={response.status_code}, 좌표=({lat}, {lng})")
    except Exception as e:
        print(f"❌ 예외 발생: {e} / 좌표=({lat}, {lng})")
    return None

# ✅ 메인 함수
def main():
    print("📥 데이터 불러오는 중...")
    df = pd.read_csv("/Users/leejuan/Desktop/이어드림스쿨/코딩테스트 문제풀이/senior-traffic-accident/all_accident_info_combined.csv", low_memory=False)
    df = df[['lat', 'lng']].dropna().head(50).reset_index(drop=True)

    # ✅ 도로명 추출
    road_names = []
    for i, row in df.iterrows():
        print(f"🛣️ {i+1}/{len(df)} 도로명 추출 중...")
        road_name = get_road_name(row['lat'], row['lng'])
        road_names.append(road_name)

    df['도로명'] = road_names
    df = df.dropna(subset=['도로명'])
    print(f"📌 도로명 추출 완료! 총 {len(df)}건 유효")

    # ✅ 스코어링 (도로별 사고건수 → 위험등급)
    road_score = df['도로명'].value_counts().reset_index()
    road_score.columns = ['도로명', '사고건수']

    bins = [0, 2, 5, 10, 20, float('inf')]
    labels = [1, 2, 3, 4, 5]  # 1=안전 ~ 5=매우 위험
    road_score['위험등급'] = pd.cut(road_score['사고건수'], bins=bins, labels=labels)

    score_dict = dict(zip(road_score['도로명'], road_score['위험등급']))

    # ✅ 지도 시각화
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=12)
    for _, row in df.iterrows():
        grade = score_dict.get(row['도로명'])
        if grade:
            color = ['green', 'lightblue', 'orange', 'red', 'darkred'][int(grade) - 1]
            folium.CircleMarker(
                location=[row['lat'], row['lng']],
                radius=4,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=f"{row['도로명']} / 위험등급: {grade}"
            ).add_to(m)

    # ✅ 지도 저장
    m.save("scoring_map_debug.html")
    print("✅ scoring_map_debug.html 저장 완료!")
    print(df['도로명'].value_counts().head(10))
    print(f"📦 시각화된 총 좌표 수: {df.shape[0]}")

if __name__ == "__main__":
    main()
