import csv
from django.http import HttpResponse


def export_stock_balance_csv(mode, rows, cd=None):
    """
    Export stock balance data to CSV file.

    Args:
        mode (str): "period" or "current"
        rows (list): list of dicts with stock balance data
        cd (dict|None): cleaned_data dict from form (for date range in filename)

    Returns:
        HttpResponse: CSV response ready for download
    """
    response = HttpResponse(content_type="text/csv")

    # Filename
    if mode == "period" and cd:
        fname = f"stock_balance_{cd.get('date_from')}_{cd.get('date_to')}.csv"
    else:
        fname = "stock_balance_current.csv"
    response["Content-Disposition"] = f'attachment; filename="{fname}"'

    writer = csv.writer(response)

    # Headers + rows
    if mode == "period":
        writer.writerow(["Місце", "Культура", "Завезено (kg)", "Вивезено (kg)", "Залишок (kg)"])
        for r in rows:
            writer.writerow([
                r["place_name"],
                r["culture"],
                r.get("in_net") or 0,
                r.get("out_net") or 0,
                r["balance"],
            ])
    else:  # current
        writer.writerow(["Місце", "Культура", "Залишок (kg)"])
        for r in rows:
            writer.writerow([
                r["place_name"],
                r["culture"],
                r["balance"],
            ])

    return response


def export_daily_report_csv(report, date, group_by):
    """
    Export daily report to CSV.

    Args:
        report (dict): результат з aggregate_rows()
        date (datetime.date): вибрана дата
        group_by (str): поле групування

    Returns:
        HttpResponse: CSV файл для завантаження
    """
    response = HttpResponse(content_type="text/csv")
    fname = f"daily_report_{date.isoformat()}.csv"
    response["Content-Disposition"] = f'attachment; filename="{fname}"'

    writer = csv.writer(response)

    # --- header ---
    writer.writerow([f"Група ({group_by})", "Культура", "Брутто (kg)", "Тара (kg)", "Нетто (kg)"])

    # --- rows ---
    for r in report["table_rows"]:
        writer.writerow([r["group"], r["culture"], r["gross"], r["tare"], r["net"]])

    # --- totals block ---
    writer.writerow([])
    writer.writerow(["", "", "Брутто завезено", report["totals"]["gross_in"]])
    writer.writerow(["", "", "Брутто вивезено", report["totals"]["gross_out"]])
    writer.writerow(["", "", "Нетто завезено", report["totals"]["net_in"]])
    writer.writerow(["", "", "Нетто вивезено", report["totals"]["net_out"]])
    writer.writerow(["", "", "Загальний залишок", report["totals"]["balance"]])

    return response
