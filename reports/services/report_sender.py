import requests
import base64
from django.conf import settings



class ReportSenderError(Exception):
    pass


class ReportSenderService:
    
    @staticmethod
    def send_pdf(file_field, metadata: dict):
        url = settings.REPORT_SERVER_URL + "/api/reports"

        with file_field.open("rb") as f:
            pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "report_type": metadata["report_type"],
            "source": "kolos",
            "payload": metadata,
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