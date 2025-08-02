import os
from flask import Flask, request, Response
from functools import wraps
from twilio.request_validator import RequestValidator

app = Flask(__name__)

# Load Basic Auth credentials from environment
WEBHOOK_USER = os.environ.get("WEBHOOK_USER")
WEBHOOK_PASS = os.environ.get("WEBHOOK_PASS")

# Twilio Auth Token (for signature validation)
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

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
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    request_valid = validator.validate(
        request.url,
        request.form,
        request.headers.get("X-Twilio-Signature", "")
    )
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
    print("🔔 /webhook was called")
    print("Headers:", dict(request.headers))
    print("URL:", request.url)
    print("Form data:", request.form)

    if not is_valid_twilio_request(request):
            print("❌ Twilio signature check failed")
    return Response("Invalid signature", status=403)

    from_number = request.form.get("From")
    body = request.form.get("Body")

    print(f"Message from {from_number}: {body}")

    # Reply message (for TwiML)
    response_message = f"Echo: {body}"
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_message}</Message>
</Response>"""
    return Response(twiml, mimetype="application/xml")

@app.route("/admin")
def admin_panel():
    return "Welcome to the admin panel."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)