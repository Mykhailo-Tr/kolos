# reports/send_utils.py
import io
import csv
import json
import logging
from django.conf import settings
import requests
from typing import Tuple


logger = logging.getLogger(__name__)


def generate_daily_csv_string(report: dict, date) -> str:
    """
    Повертає CSV як str для daily report
    """
    out = io.StringIO()
    writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
    
    # заголовок
    writer.writerow([
        f"Група ({report.get('group_by', 'none')})",
        "Культура",
        "Брутто (kg)",
        "Тара (kg)",
        "Нетто (kg)"
    ])
    
    # рядки таблиці
    for r in report.get("table_rows", []):
        group = r.get("group") or ""
        culture = r.get("culture") or ""
        gross = float(r.get("gross") or 0)
        tare = float(r.get("tare") or 0)
        net = float(r.get("net") or 0)
        writer.writerow([group, culture, gross, tare, net])
    
    # пустий рядок
    writer.writerow([])
    
    totals = report.get("totals", {})
    writer.writerow(["", "", "Брутто завезено", float(totals.get("gross_in", 0))])
    writer.writerow(["", "", "Брутто вивезено", float(totals.get("gross_out", 0))])
    writer.writerow(["", "", "Нетто завезено", float(totals.get("net_in", 0))])
    writer.writerow(["", "", "Нетто вивезено", float(totals.get("net_out", 0))])
    writer.writerow(["", "", "Загальний залишок", float(totals.get("balance", 0))])

    print(report)
    print("Generated CSV: ", out.getvalue())
    return out.getvalue()

def generate_stock_balance_csv_string(mode: str, rows: list, cd: dict = None) -> Tuple[str, str]:
    """
    Повертає (filename, csv_string)
    mode = "period" або "current"
    """
    out = io.StringIO()
    writer = csv.writer(out)
    if mode == "period":
        writer.writerow(["Місце", "Культура", "Завезено (kg)", "Вивезено (kg)", "Залишок (kg)"])
        for r in rows:
            writer.writerow([r.get("place_name"), r.get("culture"), r.get("in_net") or 0, r.get("out_net") or 0, r.get("balance")])
        fname = f"stock_balance_{cd.get('date_from')}_{cd.get('date_to')}.csv" if cd else "stock_balance_period.csv"
    else:
        writer.writerow(["Місце", "Культура", "Залишок (kg)"])
        for r in rows:
            writer.writerow([r.get("place_name"), r.get("culture"), r.get("balance")])
        fname = "stock_balance_current.csv"
    return fname, out.getvalue()


def send_report_to_server(name: str, content: str, as_json: bool = False, date_from: str = None, date_to: str = None) -> dict:
    """
    Відправляє на REPORT_SERVER_URL/api/reports/upload
    Повертає dict з результатом: {"ok": bool, "status_code": int, "response": <text_or_json>, "error": <message>}
    """
    url = settings.REPORT_SERVER_URL.rstrip("/") + "/api/reports/upload"
    headers = {"User-Agent": "Django-Report-Sender/1.0"}
    if settings.REPORT_SERVER_API_KEY:
        headers["Authorization"] = f"Bearer {settings.REPORT_SERVER_API_KEY}"
    payload = {"name": name, "content": content, "date_from": date_from, "date_to": date_to}
    try:
        # надсилаємо JSON (Flask-сервер з вашого прикладу приймає JSON)
        resp = requests.post(url, json=payload, headers=headers, timeout=getattr(settings, "REPORT_SERVER_REQUEST_TIMEOUT", 10))
        try:
            data = resp.json()
        except ValueError:
            data = resp.text
        ok = resp.status_code in (200, 201)
        return {"ok": ok, "status_code": resp.status_code, "response": data, "error": None if ok else f"HTTP {resp.status_code}"}
    except requests.RequestException as e:
        logger.exception("Failed to send report to server")
        return {"ok": False, "status_code": None, "response": None, "error": str(e)}
