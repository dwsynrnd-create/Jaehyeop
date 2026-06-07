# Jaehyeop · 할 일 관리 (To-Do App)

의존성 없이 브라우저에서 바로 작동하는 할 일 관리 웹앱입니다.
순수 HTML / CSS / JavaScript로 만들었고, 빌드 과정이나 설치가 필요 없습니다.

## 실행 방법

`index.html` 파일을 브라우저로 열기만 하면 됩니다.

```bash
# macOS
open index.html
# Linux
xdg-open index.html
# Windows
start index.html
```

## 기능

- **추가**: 입력창에 내용을 적고 Enter 또는 "추가" 버튼
- **완료 처리**: 체크박스를 누르면 취소선과 함께 완료 표시
- **삭제**: 각 항목의 `×` 버튼으로 개별 삭제
- **필터**: 전체 / 진행 중 / 완료 보기 전환
- **완료 항목 비우기**: 끝낸 일들을 한 번에 정리
- **자동 저장**: 브라우저 localStorage에 저장되어 새로고침해도 유지

## 파일 구성

| 파일 | 역할 |
| --- | --- |
| `index.html` | 화면 구조 (마크업) |
| `style.css` | 다크 테마 스타일 |
| `app.js` | 동작 로직 + localStorage 저장 |
