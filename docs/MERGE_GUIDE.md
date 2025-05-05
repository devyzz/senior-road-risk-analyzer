# 🔀 Git 브랜치 병합 가이드 (MERGE_GUIDE)

이 문서는 `senior-road-risk-analyzer` 프로젝트의 Git 브랜치 병합 전략과 PR 생성 방법을 정리한 문서입니다. 안정적인 협업을 위해 반드시 이 흐름을 따라 주세요.

---

## ✅ 병합 순서 (Merge Flow)

```plaintext
작업 브랜치 (예: docs/add-docs)
          ↓
       dev 브랜치
          ↓
       main 브랜치
```

---

## 🧭 1. 작업 브랜치 → dev 브랜치로 PR

### ✔️ 조건

- 작업 완료
- 커밋 정리 완료 (`git rebase` 또는 squash 병합 권장)
- 로컬에서 테스트 완료

### 🛠 PR 생성 방법

1. GitHub 저장소 접속 (예: https://github.com/devyzz/senior-road-risk-analyzer)
2. 작업 후 `git push` 완료되면 상단에 `Compare & pull request` 버튼 클릭
3. PR 대상 브랜치 확인
   - **base**: `dev`
   - **compare**: `작업 브랜치`
4. PR 제목 작성 (예: `docs: 협업 가이드 문서 추가`)
5. 변경 내용 요약 작성 (무엇을, 왜 변경했는지)
6. 팀원에게 리뷰 요청
7. 승인되면 `dev` 브랜치에 merge

### 💻 관련 Git 명령어

```bash
# dev 브랜치 기준으로 새 작업 브랜치 생성
git checkout dev
git pull origin dev
git checkout -b docs/add-docs

# 작업 후 커밋 & 푸시
git add .
git commit -m "docs: 협업 가이드 문서 추가"
git push -u origin docs/add-docs
```

---

## 🧪 2. dev 브랜치 통합 테스트

- 모든 작업 브랜치가 dev로 모인 후, 통합 테스트 수행
- 버그나 충돌 있으면 해당 작업 브랜치에서 수정 후 재병합

### 💻 관련 Git 명령어

```bash
# dev 최신 내용 확인
git checkout dev
git pull origin dev

# 충돌 해결 후 다시 push
# (필요한 경우)
```

---

## 🚀 3. dev → main 브랜치로 PR (배포 단계)

### ✔️ 조건

- 통합 테스트 통과
- 릴리스 준비 완료 상태

### 🛠 PR 생성 방법

1. GitHub에서 새 PR 생성
2. Base: `main`, Compare: `dev`
3. PR 제목 예시: `Release: 1차 분석 결과 업로드`
4. 리뷰 후 병합 → `main`은 항상 안정된 상태 유지

### 💻 관련 Git 명령어

```bash
# main 브랜치 최신 상태 확인
git checkout main
git pull origin main

# dev에서 변경사항 병합
git merge dev

# 병합 후 push
git push origin main
```

---

## ⚠️ 주의사항

- 직접 `main`에 작업 절대 금지 ❌
- 병합 전 반드시 `dev` 최신 상태로 pull 받을 것
- 충돌(conflict) 발생 시 작업자 스스로 해결
- PR에는 **변경 이유 및 목적**을 꼭 적을 것

---

함께 깔끔하게 협업해요! 🐰