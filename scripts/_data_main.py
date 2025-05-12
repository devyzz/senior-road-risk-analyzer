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
