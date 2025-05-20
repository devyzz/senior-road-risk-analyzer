import pandas as pd
import matplotlib.pyplot as plt
# 한글 폰트 설정 (Mac 기준)
plt.rc('font', family='AppleGothic')  # 한글 깨짐 방지용
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지
import seaborn as sns

# CSV 파일 불러오기
file_path = "./data/processed/accident_data_filtered.csv"
df = pd.read_csv(file_path)
df['traffic_volume'] = pd.to_numeric(df['traffic_volume'], errors='coerce')

# route_nm별 사고건수 포함
accident_by_route = (
    df.dropna(subset=["route_nm"])
      .groupby("route_nm")
      .agg(
          평균교통량=("traffic_volume", "mean"),
          고령자핫스팟건수=("elderly_hotspot", "sum"),
          사고건수=("route_nm", "count")
      )
      .reset_index()
      .sort_values("사고건수", ascending=False)
)

print(accident_by_route.head(20))  # 상위 20개 출력

fig, ax1 = plt.subplots(figsize=(12, 6))

compare_df = accident_by_route.head(10)

# 첫 번째 축: 평균 교통량 막대그래프
sns.barplot(data=compare_df, x="route_nm", y="평균교통량", ax=ax1, color='skyblue')
ax1.set_ylabel("평균교통량", color='skyblue')
ax1.tick_params(axis='y', labelcolor='skyblue')
ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha='right')

# 두 번째 축: 고령자핫스팟건수 선그래프
ax2 = ax1.twinx()
sns.lineplot(data=compare_df, x="route_nm", y="고령자핫스팟건수", ax=ax2, color='red', marker='o')
ax2.set_ylabel("고령자핫스팟건수", color='red')
ax2.tick_params(axis='y', labelcolor='red')

plt.title("도로별 평균교통량과 고령자 핫스팟 건수 (이중축 비교)")
plt.tight_layout()
plt.show()