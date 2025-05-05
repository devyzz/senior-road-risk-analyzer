# 📘 Git 협업 브랜치 전략 및 작업 가이드

이 문서는 `senior-road-risk-analyzer` 프로젝트에서 팀원들이 효율적으로 협업하기 위한 Git 브랜치 전략과 사용 방법을 설명합니다.

---

## 브랜치 구조

```plaintext
main                    # 최종 배포용 (완성된 코드만)
├── dev                 # 통합 개발 브랜치 (작업 통합 및 테스트)
│   ├── data-prep/xxx   # 데이터 전처리
│   ├── analysis/xxx    # 위험지표 분석
│   ├── web/xxx         # 웹 프론트/백 개발
│   └── docs/xxx        # 발표자료 및 문서 작업
```

## 브랜치 생성 및 작업 가이드

### 1. dev 브랜치에서 시작

```bash
git checkout dev
git pull origin dev
```

### 2. 작업 브랜치 생성 및 이동

```bash
git checkout -b docs/add-docs # 없는 브랜치를 새로 생성하는 경우는 -b 옵션
git checkout  docs/add-docs
```
#### <span style="color:#F24405">브랜치 네이밍 규칙</span>
 목적별로 브랜치를 구분하기 위해서 네이밍 컨벤션을 사용해보아용! 🐰
 | 브랜치 용도   | 네이밍 예시                 |
 | ------------- | --------------------------- |
 | 데이터 전처리 | `data-prep/작업명`   |
 | 위험지표 분석 및 모델링 | `analysis/작업명` |
 | 웹 개발       | `web/작업명`   |
 | 문서 작업     | `docs/작업명`   |


### 3. 작업 후 커밋

```bash
git add .   # 현재폴더를 기준으로 이하의 모든 변경파일을 git 스테이지에 올림
git add docs/TEAM_GUIDE.md # 특정 변경 파일만 올리고 싶을 경우 add 뒤에 이렇게 파일명 명시
git commit -m "docs: TEAM_GUIDE 추가"
```

#### <span style="color:#F24405">커밋 컨밴션</span>
작업 이유와 내용파악의 용이성을 확보하기 위해 우리 모두 커밋컨밴션을 지켜서 메세지를 작성해보아요
| 태그       | 설명                           | 예시                                    |
|------------|--------------------------------|-----------------------------------------|
| `feat`     | 새로운 기능 추가             | `feat: 사용자 로그인 기능 구현`         |
| `fix`      | 버그 수정                    | `fix: 날짜 포맷 오류 수정`              |
| `docs`     | 문서 작업                    | `docs: README에 설명 추가`              |
| `refactor` | 코드 리팩토링 (기능 변경 X)  | `refactor: 중복 로직 함수화`           |
| `chore`    | 기타 설정/환경 작업          | `chore: 패키지 업데이트`               |
| `perf`     | 성능 최적화                  | `perf: 페이지 렌더링 속도 개선`         |
| `revert`   | 이전 커밋 되돌리기           | `revert: 로그인 기능 커밋 되돌림`       |


### 4. 원격 브랜치로 푸시

```bash
git push -u origin data-prep/null-cleaning
```

---

## 5. Pull Request (PR) 작성 흐름

1. GitHub 레포지토리에서 "Compare & pull request" 클릭
2. **base 브랜치: `dev`**, **compare 브랜치: 작업한 브랜치**
3. 제목, 설명, 관련 이슈 작성
4. 리뷰 요청 후 병합

⚠️ merge 방법은 [MERGE_GUIDE.md](https://github.com/devyzz/senior-road-risk-analyzer/blob/main/docs/MERGE_GUIDE.md) 확인 

## 주의사항

- `main` 브랜치에는 직접 작업 ❌
- 항상 `dev`를 기준으로 작업 브랜치를 만들 것
- PR 병합 전에 반드시 로컬 테스트 완료할 것

🐰🐰🐰 함께 효율적으로 협업해보아요! 🐰🐰🐰