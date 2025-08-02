# WhatsApp Bot via Twilio + Flask

A minimal Flask application that demonstrates how to handle incoming WhatsApp
messages using the [Twilio API](https://www.twilio.com/whatsapp).
The bot simply echoes back any message it receives and showcases both request
validation and basic route protection.

## 🚀 Features
- Receives WhatsApp messages through a Twilio webhook
- Responds with the same text using TwiML
- Secures all non-webhook routes with HTTP Basic Auth
- Validates requests with Twilio's `X-Twilio-Signature`
- Dockerfile and CapRover descriptor for easy deployment

## 📋 Requirements
- Python 3.11+
- A Twilio account with access to the WhatsApp sandbox or a WhatsApp-enabled number
- (Optional) [CapRover](https://caprover.com/) if you want to deploy

## 📁 Project Structure
```
.
├── app.py              # Flask application
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image definition
├── captain-definition  # CapRover deployment descriptor
└── README.md           # This file
```

## 🔧 Configuration
The application relies on the following environment variables:

| Variable | Description |
|----------|-------------|
| `TWILIO_ACCOUNT_SID` | Your Twilio account SID (required if you extend the bot to send messages) |
| `TWILIO_AUTH_TOKEN` | Twilio auth token used to verify request signatures |
| `TWILIO_WHATSAPP_NUMBER` | WhatsApp number in the form `whatsapp:+14155238886` |
| `WEBHOOK_USER` | Username for HTTP Basic Auth |
| `WEBHOOK_PASS` | Password for HTTP Basic Auth |

Set these variables locally (e.g. in a `.env` file or via your shell) or in
CapRover's *App Configs → Environment Variables* panel.

## 🛠️ Running Locally
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Expose the running server to the internet (for example with
[ngrok](https://ngrok.com/)) and configure your Twilio sandbox to send webhooks
to `https://<public-url>/webhook`.

## ☸️ Deployment (CapRover)
1. Create a new application in CapRover (e.g. `whatsappbot`).
2. Set the environment variables listed above.
3. Deploy via the CapRover UI or by pushing this repository.
4. Enable HTTPS and update your Twilio webhook to point to `/webhook` on the new domain.

## 🧪 Testing
1. Join the Twilio sandbox (send the provided keyword to the sandbox number).
2. Send a WhatsApp message to your Twilio sandbox number.
3. The bot will reply with the same text and log details to the console.

## 🔐 Security Notes
- `/webhook` only accepts requests that pass Twilio signature validation.
- All other routes require HTTP Basic Auth—change the default credentials before deploying.

## 📝 License
MIT
