"""NTIS 사업공고 RSS를 받아 data.json에 쌓는 프로그램.

원래 aaayoung01/ntis-notice의 crawler.py를 바탕으로, 수집이 조용히 멈추던 문제를 고쳤다.
- 접속 대기 시간(timeout)과 브라우저처럼 보이는 접속 정보(User-Agent)를 넣음
- 실패하면 몇 번 다시 시도하고, https/http 두 주소를 모두 시도함
- 끝까지 실패하면 '실패'로 끝내서 GitHub가 메일로 알려 주게 함(전에는 오류를 숨기고 성공으로 끝남)
- 마지막 수집 결과를 meta.json에 남겨 웹페이지에 '마지막 수집 시각'을 보여 줌
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET

import requests

RSS_URLS = [
    "https://www.ntis.go.kr/rndgate/unRndRss.xml?prt=100",
    "http://www.ntis.go.kr/rndgate/unRndRss.xml?prt=100",
]
# 웹페이지 필터에 보이는 부처. 여기에 없는 부처의 공고는 버리지 않고 '기타'로 넣는다.
MAIN_DEPTS = ["과학기술정보통신부", "교육부", "보건복지부", "산업통상부", "식품의약품안전처", "질병관리청"]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
DATA_FILE = "data.json"
META_FILE = "meta.json"
KST = timezone(timedelta(hours=9))


def format_date(date_str):
    if not date_str:
        return ""
    digits = re.sub(r"\D", "", date_str)
    return f"{digits[:4]}.{digits[4:6]}.{digits[6:8]}" if len(digits) >= 8 else date_str


def format_budget(amount_str):
    if not amount_str:
        return "-"
    digits = re.sub(r"\D", "", amount_str)
    if not digits:
        return amount_str
    val = int(digits)
    if val == 0:
        return "0원"
    mil = val // 1000000
    return f"{val:,}원" if mil == 0 else f"{mil:,}백만원"


def fetch_rss():
    """RSS를 받아 온다. 주소 2개 × 최대 4번 시도. 실패 이유를 모아 돌려준다."""
    errors = []
    for attempt in range(4):
        for url in RSS_URLS:
            try:
                res = requests.get(url, headers=HEADERS, timeout=40)
                res.raise_for_status()
                root = ET.fromstring(res.content)  # XML이 아니면 여기서 오류
                if root.find(".//item") is None:
                    raise ValueError("RSS에 공고(item)가 하나도 없음")
                return root, errors
            except Exception as e:  # noqa: BLE001
                errors.append(f"{attempt + 1}회차 {url}: {type(e).__name__}: {e}"[:300])
        time.sleep(20 * (attempt + 1))
    return None, errors


def parse_items(root):
    items = []
    for item in root.findall(".//item"):
        raw_dept = (item.findtext("author") or "-").strip()
        appbegin = format_date(item.findtext("appbegin") or item.findtext("appBegin") or "")
        appdue = format_date(item.findtext("appdue") or item.findtext("appDue") or "")
        items.append({
            "department": raw_dept if raw_dept in MAIN_DEPTS else "기타",
            "ministry": raw_dept,
            "title": (item.findtext("title") or "제목 없음").strip(),
            "link": (item.findtext("link") or "#").strip(),
            "agency": (item.findtext("category") or "-").strip(),
            "date": format_date(item.findtext("pubDate") or ""),
            "appPeriod": f"{appbegin} ~ {appdue}" if appbegin and appdue else "-",
            "appBegin": appbegin,
            "appDue": appdue,
            "amount": format_budget(item.findtext("budget") or ""),
        })
    return items


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)


def main():
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    meta = load_json(META_FILE, {})
    meta["lastRun"] = now

    root, errors = fetch_rss()
    if root is None:
        meta["lastResult"] = "실패"
        meta["lastError"] = errors[-1] if errors else "알 수 없음"
        save_json(META_FILE, meta)
        print("NTIS RSS 수집 실패:\n" + "\n".join(errors))
        sys.exit(1)  # 실패로 끝내야 GitHub가 알림 메일을 보냄

    new_items = parse_items(root)
    data = load_json(DATA_FILE, [])
    by_link = {d.get("link"): d for d in data}
    added = 0
    for item in reversed(new_items):  # 오래된 것부터 넣어 최신 공고가 맨 위로 오게
        old = by_link.get(item["link"])
        if old is None:
            data.insert(0, item)
            by_link[item["link"]] = item
            added += 1
        else:
            old.update(item)  # 접수기간 변경 등 정정 반영

    save_json(DATA_FILE, data)
    meta.update({
        "lastResult": "성공",
        "lastSuccess": now,
        "lastAdded": added,
        "rssItems": len(new_items),
        "total": len(data),
        "latestNoticeDate": max((d.get("date", "") for d in data), default=""),
    })
    meta.pop("lastError", None)
    save_json(META_FILE, meta)
    print(f"성공: RSS {len(new_items)}건 중 새 공고 {added}건 추가, 전체 {len(data)}건")


if __name__ == "__main__":
    main()
