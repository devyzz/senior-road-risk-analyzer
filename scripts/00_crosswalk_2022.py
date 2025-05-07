#──────────────────────────────────────────────────────────────
#  횡단보도 데이터 수집
#
# - 내용 : 2022년도 서울시 자치구별 신호등 개수 집계 및 시각화
# - 데이터 : 서울특별시_보행등 위도 경도 현황_20220919.csv
# - 출처 : 서울 열린데이터 광장
# - 도구 : pandas, matplotlib, folium
# - 작성자 : 이주안
# - 작성일 : 2025.05.07
# - 수정자 : 이주안
# - 수정일 : 2025.05.07
# - 수정내용 : 
#   - 자치구별 신호등 개수 집계 및 시각화
# ──────────────────────────────────────────────────────────────

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import folium

# 한글 폰트 설정 (예: Apple 기본 폰트 사용)
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# 파일 경로 및 데이터 로드
file_path = "/Users/leejuan/Desktop/교통국토경진대회/02. data/서울특별시_보행등 위도 경도 현황_20220919.csv"
df_signal = pd.read_csv(file_path, encoding='euc-kr')

# 데이터 확인용 출력
#print(df_signal.head())
#print(df_signal.columns) 
#print(df_signal.info())
#print(df_signal['자치구'].unique())

# 자치구별 신호등 개수 집계
gu_counts = df_signal['자치구'].value_counts().sort_values(ascending=False)

# 자치구별 보행등 설치 개수 통계
print("=== 자치구별 보행등 설치 개수 통계 ===")
print(f"총 자치구 수: {gu_counts.count()}")
print(f"총 보행등 수: {gu_counts.sum()}")
print(f"최소값: {gu_counts.min()}개 (구: {gu_counts.idxmin()})")
print(f"최대값: {gu_counts.max()}개 (구: {gu_counts.idxmax()})")
print(f"평균값: {gu_counts.mean():.2f}개")
print(f"중앙값: {gu_counts.median()}개")
print(f"표준편차: {gu_counts.std():.2f}")
# 상위 및 하위 5개 자치구
print("\n=== 보행등 개수 상위 5개 자치구 ===")
print(gu_counts.head(5))
print("\n=== 보행등 개수 하위 5개 자치구 ===")
print(gu_counts.tail(5))

# 시각화: 자치구별 보행등 설치 개수
plt.figure(figsize=(12, 6))
gu_counts.plot(kind='bar', color='skyblue')
plt.title('자치구별 보행등(신호등) 설치 개수')
plt.xlabel('자치구')
plt.ylabel('보행등 개수')
plt.xticks(rotation=45)
plt.tight_layout()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# 지도 중심 좌표 (서울시청 기준)
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
# 신호등 위치 마커 추가
for _, row in df_signal.iterrows():
    folium.CircleMarker(
        location=[row['위도'], row['경도']],
        radius=1,
        color='red',
        fill=True,
        fill_opacity=0.7
    ).add_to(m)
# 지도 저장
m.save("signal_map_seoul.html")
print("✅ 지도 저장 완료: signal_map_seoul.html")