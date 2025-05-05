# 📘 Git 협업 브랜치 전략 및 작업 가이드

이 문서는 `senior-road-risk-analyzer` 프로젝트에서 팀원들이 효율적으로 협업하기 위한 Git 브랜치 전략과 사용 방법을 설명합니다.

---

## ✅ 브랜치 구조

```plaintext
main                    # 🔒 최종 배포용 (완성된 코드만)
├── dev                 # 🧪 통합 개발 브랜치 (작업 통합 및 테스트)
│   ├── data-prep/xxx   # 📊 데이터 전처리
│   ├── analysis/xxx    # 📈 위험지표 분석
│   ├── web/xxx         # 💻 웹 프론트/백 개발
│   └── docs/xxx        # 📝 발표자료 및 문서 작업
```

---

## ✅ 브랜치 생성 및 작업 가이드

### 1. dev 브랜치에서 시작

```bash
git checkout dev
git pull origin dev
```

### 2. 새 브랜치 생성 (예: 데이터 전처리 작업)

```bash
git checkout -b data-prep/null-cleaning
```

### 3. 작업 후 커밋

```bash
git add .
git commit -m "결측치 처리 notebook 추가"
```

### 4. 원격 브랜치로 푸시

```bash
git push -u origin data-prep/null-cleaning
```

---

## ✅ Pull Request (PR) 작성 흐름

1. GitHub 레포지토리에서 "Compare & pull request" 클릭
2. **base 브랜치: `dev`**, **compare 브랜치: 작업한 브랜치**
3. 제목, 설명, 관련 이슈 작성
4. 리뷰 요청 후 병합

---

## ✅ 브랜치 네이밍 규칙

| 브랜치 용도   | 네이밍 예시                 |
| ------------- | --------------------------- |
| 데이터 전처리 | `data-prep/작업명`   |
| 위험지표 분석 | `analysis/작업명` |
| 웹 개발       | `web/작업명`   |
| 문서 작업     | `docs/작업명`   |

---

## ✅ 주의사항

- `main` 브랜치에는 직접 작업 ❌
- 항상 `dev`를 기준으로 작업 브랜치를 만들 것
- PR 병합 전에 반드시 로컬 테스트 완료할 것

---

함께 효율적으로 협업합시다! 💪