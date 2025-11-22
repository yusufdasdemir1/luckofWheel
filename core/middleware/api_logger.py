import time
import json
from core.models import APILog

MAX_NORMAL = 400
MAX_ERROR = 500


def truncate(text, max_len):
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "... (truncated)"


def sanitize_request_body(body_text):
    try:
        data = json.loads(body_text)
    except:
        return body_text

    sensitive_keys = [
        "password", "pass", "pwd",
        "secret", "token",
        "access_token", "refresh_token",
        "new_password", "old_password"
    ]

    for key in sensitive_keys:
        if key in data:
            data[key] = "******"

    return json.dumps(data)


class APILogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        start_time = time.time()

        # --- REQUEST BODY ---
        try:
            if request.body:
                raw_body = request.body.decode("utf-8")
                safe_body = sanitize_request_body(raw_body)
                request_body = truncate(safe_body, MAX_NORMAL)
            else:
                request_body = ""
        except:
            request_body = "Unable to read request body"

        # --- RESPONSE ---
        try:
            response = self.get_response(request)
            error_occurred = False
        except Exception as e:
            error_occurred = True
            response = None
            response_body = f"Exception: {str(e)}"

        duration = round((time.time() - start_time) * 1000, 2)

        # --- RESPONSE BODY ---
        if response:
            try:
                if hasattr(response, "data"):
                    body = json.dumps(response.data)
                else:
                    body = response.content.decode("utf-8")
            except:
                body = ""

            if response.status_code >= 500:
                level = "ERROR"
                response_body = truncate(body, MAX_ERROR)
            elif response.status_code >= 400:
                level = "WARNING"
                response_body = truncate(body, MAX_NORMAL)
            else:
                level = "INFO"
                response_body = truncate(body, MAX_NORMAL)
        else:
            level = "ERROR"
            response_body = response_body

        # --- SAVE TO DB ---
        try:
            APILog.objects.create(
                log_level=level,
                path=request.path,
                method=request.method,
                status=(response.status_code if response else 500),
                ip=request.META.get("REMOTE_ADDR", ""),
                duration=duration,
                request_body=request_body,
                response_body=response_body,
            )
        except Exception as e:
            print("APILog save error:", e)

        if error_occurred:
            raise

        return response
