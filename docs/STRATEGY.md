# STRATEGY.md

TodoList 프로젝트 설계 원칙 + LLM 하네스 방어 전략.

## 프로젝트 목적

미니멀 TodoList 웹 앱. "AI가 만든 것 같지 않은" UX가 핵심.
MUJI 스타일 — 꾸미지 않아서 아름다운 것.

## 설계 원칙 4가지

1. **UX 최우선**: 기능보다 사용성. 색상 5가지 이내, gradient 금지, 이모지 금지.
2. **보안 기본**: SQL 파라미터 바인딩, XSS 방지(textContent), 입력 검증(Pydantic).
3. **접근성**: 터치 타겟 ≥ 44px, 키보드 내비게이션, 충분한 색상 대비.
4. **테스트 신뢰성**: 실제 DB로 통합 테스트. 목(mock) 사용 금지.

## 하네스 방어 8가지

① **할루시네이션 방어**: 함수 호출 전에 시그니처를 grep으로 확인. 모르면 읽는다. 가정하지 않는다.

② **확증 편향 방어**: 같은 접근 2번 실패 시 접근 자체를 바꾼다. 3번째 시도 금지. 실패 시 "왜 실패했는가"를 먼저 진단한다.

③ **유령 수정 방어**: 수정 후 반드시 `make test` 실행. "논리적으로 맞을 것"을 신뢰하지 않는다.

④ **스코프 팽창 방어**: Issue에 정의된 수락 조건만 구현한다. "이것도 같이 하면 좋겠다"는 하지 않는다.

⑤ **숫자 전파 방어**: 숫자 변경 시 `grep -ri "이전값"` 전수 검색. CLAUDE.md, README, 코드 모두 확인.

⑥ **테스트 환각 방어**: pytest-asyncio fixture는 반드시 `@pytest_asyncio.fixture` 사용. 조건부 로직 안에 핵심 assertion을 넣지 않는다.

⑦ **보안 정책 위반 방어**: CLAUDE.md에 "f-string SQL 금지"라면 코드에서도 금지. 화이트리스트라도 f-string으로 SQL 생성 금지. 정책을 바꾸고 싶으면 CLAUDE.md를 수정한다. 코드에 예외를 넣지 않는다.

⑧ **접근성 누락 방어**: 시각적 크기가 작으면 `::after` pseudo-element로 히트 영역 확장. 터치 타겟 ≥ 44px (WCAG).

## 품질 기준 (Evaluation Checklist)

```bash
# 기능
make test                                              # 14/14 PASS

# 코드 품질
grep -c "def " app/database.py                        # ≥ 7
grep -c '"""' app/routers/todos.py                    # ≥ 5

# UX 품질
grep -c "gradient" app/static/css/style.css           # → 0
grep -c "location.reload" app/static/js/app.js        # → 0

# 보안
grep -c 'f"' app/database.py                          # → 0
grep -n "innerHTML" app/static/js/app.js              # 정적 체크마크 외 없음
grep -c "field_validator" app/models.py               # ≥ 2

# 접근성
grep -c "::after" app/static/css/style.css            # ≥ 2
```
