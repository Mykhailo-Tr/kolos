import requests
import base64
from datetime import date, datetime
from decimal import Decimal
from django.conf import settings


def make_json_safe(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}

    if isinstance(value, list):
        return [make_json_safe(v) for v in value]

    return value



class ReportSenderError(Exception):
    pass


class ReportSenderService:
    
    @staticmethod
    def send_pdf(file_field, metadata: dict):
        url = settings.REPORT_SERVER_URL + "/api/reports"

        with file_field.open("rb") as f:
            pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

        safe_metadata = make_json_safe(metadata)

        payload = {
            "report_type": safe_metadata["report_type"],
            "source": "kolos",
            "payload": safe_metadata,
            "filename": safe_metadata.get("filename"),
            "pdf_base64": pdf_base64,
        }

        response = requests.post(
            url,
            json=payload,   # ✅ JSON!
            timeout=10
        )

        if response.status_code == 409:
            return "duplicate"

        response.raise_for_status()
        return "ok"