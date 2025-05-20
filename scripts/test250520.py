import pandas as pd
import matplotlib.pyplot as plt
 # 한글 폰트 설정 (Mac 기준)
plt.rc('font', family='AppleGothic')  # 한글 깨짐 방지용
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지
import seaborn as sns
# CSV 불러오기
file_path = "./data/processed/accident_data_filtered.csv"
df = pd.read_csv(file_path)

# route_nm별 평균 속도 계산
speed_by_route = (
    df.dropna(subset=["route_nm", "velocity"])
      .groupby("route_nm")["velocity"]
      .mean()
      .reset_index()
      .rename(columns={"velocity": "평균속도"})
      .sort_values("평균속도", ascending=False)
)
df.info()
# route_nm별 평균 속도 및 고령자 핫스팟 수 계산
hotspot_speed_by_route = (
    df.dropna(subset=["route_nm", "velocity", "elderly_hotspot"])
      .groupby("route_nm")
      .agg(
          평균속도=("velocity", "mean"),
          고령자핫스팟건수=("elderly_hotspot", "sum")
      )
      .reset_index()
      .sort_values("고령자핫스팟건수", ascending=False)
)
hotspot_speed_by_route.info()

print(hotspot_speed_by_route.head(20))  # 상위 20개 출력

# 시각화: 도로별 평균속도와 고령자 핫스팟 건수 비교
compare_df = hotspot_speed_by_route.head(10)
compare_melted = compare_df.melt(id_vars="route_nm", value_vars=["평균속도", "고령자핫스팟건수"],
                                  var_name="지표", value_name="값")

plt.figure(figsize=(12, 6))
sns.barplot(data=compare_melted, x="값", y="route_nm", hue="지표")
plt.title("도로별 평균속도와 고령자 핫스팟 건수 비교", fontsize=14)
plt.xlabel("값")
plt.ylabel("도로명")
plt.grid(True)
plt.tight_layout()
plt.show()
plt.close()

