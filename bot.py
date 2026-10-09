"""오하아사 별자리 운세 -> 디스코드 웹훅 (하루 1회)

환경변수
  DISCORD_WEBHOOK_URL  (필수) 디스코드 웹훅 주소
  ANTHROPIC_API_KEY    (선택) 있으면 한국어로 번역해서 같이 올림
  FORCE=1              (선택) 오늘 방송분이 아니어도 강제 전송 (테스트용)
  DRY_RUN=1            (선택) 디스코드로 보내지 않고 콘솔에 출력
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

DATA_URL = "https://www.asahi.co.jp/data/ohaasa2020/horoscope.json"
JST = timezone(timedelta(hours=9))

SIGNS = {
    "01": ("♈", "양자리", "おひつじ座"), "02": ("♉", "황소자리", "おうし座"),
    "03": ("♊", "쌍둥이자리", "ふたご座"), "04": ("♋", "게자리", "かに座"),
    "05": ("♌", "사자자리", "しし座"), "06": ("♍", "처녀자리", "おとめ座"),
    "07": ("♎", "천칭자리", "てんびん座"), "08": ("♏", "전갈자리", "さそり座"),
    "09": ("♐", "사수자리", "いて座"), "10": ("♑", "염소자리", "やぎ座"),
    "11": ("♒", "물병자리", "みずがめ座"), "12": ("♓", "물고기자리", "うお座"),
}
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def http(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def fetch_today():
    raw = http(DATA_URL, headers={"User-Agent": "Mozilla/5.0"})
    day = json.loads(raw.decode("utf-8"))[0]
    today = datetime.now(JST).strftime("%Y%m%d")
    if day["onair_date"] != today and not os.getenv("FORCE"):
        return None, day["onair_date"]
    rows = []
    for d in sorted(day["detail"], key=lambda x: int(x["ranking_no"])):
        parts = d["horoscope_text"].split("\t")
        lucky = parts[-1].strip()
        msg = " / ".join(p.strip() for p in parts[:-1] if p.strip())
        rows.append({"rank": int(d["ranking_no"]), "sign": d["horoscope_st"],
                     "msg": msg, "lucky": lucky})
    return rows, day["onair_date"]


def translate(rows):
    """일본어 -> 한국어. 키가 없거나 실패하면 원문 유지."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return rows
    src = [{"i": i, "msg": r["msg"], "lucky": r["lucky"]} for i, r in enumerate(rows)]
    prompt = ("일본 아침방송 별자리 운세 문구를 자연스러운 한국어로 번역해줘. "
              "말투는 친근한 반말체('~할 수도!', '~해봐'). 이모지/하트는 그대로 두고, "
              "lucky는 아이템/색 이름만 짧게. 설명 없이 같은 구조의 JSON 배열만 출력해.\n"
              + json.dumps(src, ensure_ascii=False))
    body = json.dumps({"model": "claude-haiku-4-5-20251001", "max_tokens": 2000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    try:
        out = json.loads(http("https://api.anthropic.com/v1/messages", body, {
            "x-api-key": key, "anthropic-version": "2023-06-01",
            "content-type": "application/json"}))
        text = out["content"][0]["text"]
        tr = json.loads(text[text.index("["): text.rindex("]") + 1])
        for t in tr:
            rows[t["i"]]["msg_ko"] = t["msg"]
            rows[t["i"]]["lucky_ko"] = t["lucky"]
    except Exception as e:  # 번역 실패해도 원문으로 전송
        print(f"[warn] 번역 실패, 원문으로 전송: {e}", file=sys.stderr)
    return rows


def build_payload(rows, date):
    lines = []
    for r in rows:
        emoji, ko, ja = SIGNS[r["sign"]]
        msg = r.get("msg_ko", r["msg"])
        lucky = r.get("lucky_ko", r["lucky"])
        mark = MEDALS.get(r["rank"], f"`{r['rank']:>2}위`")
        head = (f"{mark} **{r['rank']}위 {emoji} {ko}**" if r["rank"] in MEDALS
                else f"{mark} **{emoji} {ko}**")
        lines.append(f"{head}\n{msg}\n🍀 {lucky}")
    d = datetime.strptime(date, "%Y%m%d")
    return {"embeds": [{
        "title": f"🔮 오늘의 별자리 운세 ({d.month}/{d.day})",
        "description": "\n\n".join(lines),
        "color": 0x8B5CF6,
        "footer": {"text": "출처: 朝日放送 おはよう朝日です"},
    }]}


def main():
    rows, date = fetch_today()
    if rows is None:
        print(f"오늘 방송분이 아직 없음 (사이트 최신: {date}) -> 전송 안 함")
        return
    rows = translate(rows)
    payload = build_payload(rows, date)
    if os.getenv("DRY_RUN"):
        print(payload["embeds"][0]["title"])
        print(payload["embeds"][0]["description"])
        return
    url = os.environ["DISCORD_WEBHOOK_URL"]
    http(url, json.dumps(payload).encode(), {
        "Content-Type": "application/json", "User-Agent": "ohaasa-bot"})
    print("전송 완료")


if __name__ == "__main__":
    main()
