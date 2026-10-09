# 오하아사 별자리 운세 디스코드 봇

아사히방송 おはよう朝日です 별자리 운세(JSON: `asahi.co.jp/data/ohaasa2020/horoscope.json`)를
매일 07:30(KST)에 디스코드 웹훅으로 올립니다. 월~금 방송분만 전송(당일 데이터가 없으면 스킵).

## 설정
1. 디스코드 채널 설정 → 연동 → 웹훅 생성 → URL 복사
2. 이 폴더를 GitHub 저장소로 올리고 Settings → Secrets and variables → Actions에 추가
   - `DISCORD_WEBHOOK_URL` (필수)
   - `ANTHROPIC_API_KEY` (선택, 있으면 한국어 번역)
3. Actions 탭에서 `ohaasa-daily` → Run workflow 로 수동 테스트

## 로컬 테스트
```
DRY_RUN=1 FORCE=1 python bot.py                       # 콘솔 출력만
DISCORD_WEBHOOK_URL=... FORCE=1 python bot.py         # 실제 전송
```
