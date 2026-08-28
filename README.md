# SOXL 매매장부

개인용 매매 기록 앱 두 개와, 종가·환율을 매일 자동으로 받아오는 워크플로.

| 파일 | 내용 |
|---|---|
| `index.html` | SOXL 매매장부 (메리츠증권) |
| `toss.html` | 무한매수법 장부 (토스증권) |
| `prices.json` | 종가·환율 (자동 갱신, 손대지 말 것) |
| `.github/workflows/update-prices.yml` | 평일 07:10 KST 자동 실행 |
| `scripts/fetch_prices.py` | 종가·환율 수집 스크립트 |

## 기록은 어디에 저장되나

**브라우저(localStorage)에만** 저장됩니다. 이 저장소에는 매매 기록이 들어가지 않습니다.
앱 안의 **기록 내보내기** 로 백업 파일을 받아 두세요. 새 기기에서는 **기록 불러오기** 로 복구합니다.

> ⚠️ 내보낸 백업 파일(`soxl-ledger-*.json`)은 이 저장소에 올리지 마세요. 개인 매매 내역이 들어 있습니다.

## 종가가 안 들어올 때

1. **Actions** 탭에서 워크플로가 실패했는지 확인
2. 실패했으면 로그를 보고, `Run workflow` 로 다시 실행
3. `prices.json` 의 `fetchedAt` 이 최근이면 정상

수집 출처는 Stooq → Yahoo Finance(종가), frankfurter → open.er-api(환율) 순으로 자동 대체됩니다.
