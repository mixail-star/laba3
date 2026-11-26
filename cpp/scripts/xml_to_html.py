#!/usr/bin/env python3
"""Собирает reports/*.xml (JUnit/GoogleTest) в один HTML-файл reports/index.html."""
import html
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

reports = Path(sys.argv[1] if len(sys.argv) > 1 else "reports")
files = [("GoogleTest", "gtest.xml"), ("Catch2", "catch2.xml"), ("Boost.Test", "boost.xml")]


def parse(path):
    """Возвращает список (набор, тест, статус, время, сообщение)."""
    rows = []
    for case in ET.parse(path).getroot().iter("testcase"):
        suite = case.get("classname") or ""
        status = "pass"
        msg = ""
        for tag, st in (("failure", "fail"), ("error", "fail"), ("skipped", "skip")):
            node = case.find(tag)
            if node is not None:
                status = st
                msg = (node.get("message") or "") + "\n" + (node.text or "")
        if case.get("status") == "notrun":
            status = "skip"
        try:
            t = float(case.get("time") or 0)
        except ValueError:
            t = 0.0
        rows.append((suite, case.get("name") or "", status, t, msg.strip()))
    return rows


sections, totals = [], {"pass": 0, "fail": 0, "skip": 0}
for title, name in files:
    p = reports / name
    if not p.exists():
        continue
    rows = parse(p)
    c = {k: sum(1 for r in rows if r[2] == k) for k in totals}
    for k in totals:
        totals[k] += c[k]
    body = "".join(
        f'<tr class="{s}"><td>{html.escape(su)}</td><td>{html.escape(n)}</td>'
        f'<td>{ {"pass": "OK", "fail": "FAIL", "skip": "SKIP"}[s] }</td><td>{t * 1000:.3f}</td>'
        f'<td><pre>{html.escape(m)}</pre></td></tr>'
        for su, n, s, t, m in rows
    )
    bad = " bad" if c["fail"] else ""
    sections.append(
        f'<details{" open" if c["fail"] else ""}><summary class="{bad}"><b>{title}</b> — '
        f'всего {len(rows)}, успешно {c["pass"]}, ошибок {c["fail"]}, пропущено {c["skip"]}</summary>'
        f'<table><tr><th>Набор</th><th>Тест</th><th>Статус</th><th>мс</th><th>Сообщение</th></tr>{body}</table></details>'
    )

verdict = "ВСЕ ТЕСТЫ ПРОШЛИ" if totals["fail"] == 0 else f'ОШИБОК: {totals["fail"]}'
cls = "ok" if totals["fail"] == 0 else "err"
page = f"""<!doctype html><html lang="ru"><meta charset="utf-8"><title>Результаты тестов</title>
<style>
body{{font:15px system-ui,sans-serif;margin:2rem auto;max-width:1000px;padding:0 1rem}}
.banner{{padding:1rem 1.2rem;border-radius:8px;font-size:1.3rem;font-weight:600;margin-bottom:1rem}}
.banner.ok{{background:#d8f3dc;color:#1b4332}} .banner.err{{background:#ffd6d6;color:#7a1010}}
details{{margin:.6rem 0;border:1px solid #ccc;border-radius:8px;padding:.5rem .8rem}}
summary{{cursor:pointer;padding:.2rem 0}} summary.bad{{color:#b00020}}
table{{border-collapse:collapse;width:100%;margin-top:.6rem;font-size:13px}}
th,td{{border-bottom:1px solid #e3e3e3;padding:3px 6px;text-align:left;vertical-align:top}}
tr.pass td:nth-child(3){{color:#1b7f3b;font-weight:600}} tr.fail{{background:#fff0f0}}
tr.fail td:nth-child(3){{color:#b00020;font-weight:600}} tr.skip td:nth-child(3){{color:#a06a00}}
pre{{margin:0;white-space:pre-wrap}}
</style>
<div class="banner {cls}">{verdict}: успешно {totals["pass"]}, ошибок {totals["fail"]}, пропущено {totals["skip"]}</div>
{"".join(sections)}
</html>"""
(reports / "index.html").write_text(page, encoding="utf-8")
print(f"Отчёт: {reports / 'index.html'}  ({verdict})")
sys.exit(1 if totals["fail"] else 0)
