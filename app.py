import os
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from flask import Flask, request, Response
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import openai

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
logging.basicConfig(level=logging.INFO)

# Load Basic Auth credentials from environment
WEBHOOK_USER = os.environ.get("WEBHOOK_USER")
WEBHOOK_PASS = os.environ.get("WEBHOOK_PASS")

# Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")

if not TWILIO_AUTH_TOKEN:
    app.logger.warning("TWILIO_AUTH_TOKEN is not set")

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    app.logger.warning("Twilio REST client not fully configured")

# OpenRouter API Key
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set")

openai.api_key = OPENROUTER_API_KEY
openai.api_base = "https://openrouter.ai/api/v1"

# Thread pool for background LLM calls
executor = ThreadPoolExecutor(max_workers=4)
LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "10"))

# OpenRouter model (defaults to Meta Llama 3.1 70B Instruct)
OPENROUTER_MODEL = os.environ.get(
    "OPENROUTER_MODEL", "meta-llama/Meta-Llama-3.1-70B-Instruct"
)

def check_auth(username, password):
    return username == WEBHOOK_USER and password == WEBHOOK_PASS

def authenticate():
    return Response(
        "Authentication Required", 401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow public access to /webhook (handled separately)
        if request.path == "/webhook":
            return f(*args, **kwargs)
        # Require auth for everything else
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def is_valid_twilio_request(request):
    if not TWILIO_AUTH_TOKEN:
        app.logger.error("Missing Twilio auth token")
        return False

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        app.logger.warning("X-Twilio-Signature header missing")

    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    request_valid = validator.validate(
        request.url,
        request.form,
        signature,
    )
    if not request_valid:
        app.logger.warning("Twilio signature validation failed")
    return request_valid

@app.before_request
@requires_auth
def before_request():
    pass

@app.route("/")
def index():
    return "Hello from WhatsApp bot!"

@app.route("/webhook", methods=["POST"])
def webhook():
    app.logger.info("/webhook was called")

    signature = request.headers.get("X-Twilio-Signature", "")
    app.logger.info("X-Twilio-Signature: %s", signature)

    app.logger.info("Headers: %s", dict(request.headers))
    app.logger.info("Body: %s", request.get_data(as_text=True))
    app.logger.debug("URL: %s", request.url)
    app.logger.debug("Form data: %s", request.form)

    if not is_valid_twilio_request(request):
        return Response("Invalid signature", status=403)

    from_number = request.form.get("From")
    body = request.form.get("Body")

    app.logger.info("Message from %s: %s", from_number, body)

    def generate_reply(prompt: str) -> str:
        response = openai.ChatCompletion.create(
            model=OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        if response.choices:
            return response.choices[0].message["content"].strip()
        return "Sorry, I couldn't generate a reply."

    future = executor.submit(generate_reply, body)

    try:
        response_message = future.result(timeout=LLM_TIMEOUT)
        resp = MessagingResponse()
        resp.message(response_message)
        return Response(str(resp), mimetype="application/xml")
    except TimeoutError:
        app.logger.info("LLM call timed out; sending placeholder and will reply via REST API")

        def send_delayed_reply(fut):
            try:
                final_message = fut.result()
            except Exception as exc:
                app.logger.exception("LLM call failed after timeout: %s", exc)
                final_message = "Sorry, I couldn't generate a reply."

            if twilio_client and TWILIO_WHATSAPP_NUMBER:
                try:
                    twilio_client.messages.create(
                        body=final_message,
                        from_=TWILIO_WHATSAPP_NUMBER,
                        to=from_number,
                    )
                except Exception as exc:
                    app.logger.exception("Failed to send message via Twilio REST API: %s", exc)
            else:
                app.logger.error("Twilio client not configured; cannot send delayed reply")

        future.add_done_callback(send_delayed_reply)

        resp = MessagingResponse()
        resp.message("Working on it…")
        return Response(str(resp), mimetype="application/xml")
    except Exception as exc:
        app.logger.exception("LLM processing failed: %s", exc)
        resp = MessagingResponse()
        resp.message("Sorry, I couldn't generate a reply.")
        return Response(str(resp), mimetype="application/xml")

@app.route("/admin")
def admin_panel():
    return "Welcome to the admin panel."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
