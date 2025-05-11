import subprocess

def run_script(script_name):
    print(f"===> 실행 중: {script_name}")
    result = subprocess.run(["python", script_name], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"====> 완료: {script_name}")
    else:
        print(f"⚠️ 오류 발생: {script_name}")
        print(result.stderr)

if __name__ == "__main__":
    script_paths = [
        # "scripts/fetch_source_data.py",
        # "scripts/fetch_taas_accident_data.py",
        "scripts/prepare_datasets.py"
    ]

    for script in script_paths:
        run_script(script)
print("현재 zone_df 컬럼 목록:", zone_df.columns.tolist())
if "구분" in zone_df.columns:
    sub_df = zone_df[zone_df["구분"] == zone_type]
else:
    print(f"❌ '구분' 컬럼이 없습니다. zone_type: {zone_type}")
    sub_df = pd.DataFrame()
    