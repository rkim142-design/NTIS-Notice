# NTIS 공고 모음

NTIS 사업공고 RSS(최근 100건)를 평일 하루 세 번 받아 쌓고, 웹페이지로 보여 줍니다.

## 파일
| 파일 | 하는 일 |
| --- | --- |
| `crawler.py` | NTIS RSS를 받아 `data.json`에 새 공고를 추가 (실패하면 재시도) |
| `.github/workflows/crawling.yml` | GitHub가 `crawler.py`를 자동 실행하는 일정 |
| `index.html` | 공고 목록 웹페이지 (부처·상태 필터, 검색, 의사과학자 관련 강조) |
| `data.json` | 모인 공고 목록 |
| `meta.json` | 마지막 수집 시각과 결과 (웹페이지 위쪽에 표시) |

## 자동 실행 일정
평일 한국 시간 오전 7:17, 낮 12:17, 오후 5:17
(GitHub 사정으로 몇 분~수십 분 늦게 돌 수 있음)

## 자주 하는 일
- **지금 바로 수집**: 저장소의 **Actions** 탭 → 왼쪽 `NTIS 공고 수집` → **Run workflow**
- **수집 실패 확인**: 실패하면 GitHub가 계정 메일로 알려 줌. Actions 탭에서 빨간 ✕ 기록을 누르면 이유가 보임
- **의사과학자 판단 표현 바꾸기**: `index.html`의 `FOCUS_RE` 줄
- **필터에 보이는 부처 바꾸기**: `crawler.py`의 `MAIN_DEPTS` (목록에 없는 부처는 '기타'로 들어감)

## 참고
- 공개 저장소에서 60일 동안 아무 변경이 없으면 GitHub가 자동 실행을 멈춥니다. 이 프로그램은 실행할 때마다 기록을 남기므로 보통은 해당되지 않습니다.
- 원래 [aaayoung01/ntis-notice](https://github.com/aaayoung01/ntis-notice)를 바탕으로 만들었습니다.
