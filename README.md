# WhatsApp Bot via Twilio + Flask

This is a simple WhatsApp bot built using:
- [Twilio Sandbox for WhatsApp](https://www.twilio.com/whatsapp)
- Python Flask web server
- CapRover for deployment
- Basic Authentication for admin protection
- Twilio Signature validation for security

## 🚀 Features
- Receives WhatsApp messages via Twilio webhook
- Echoes back the received message
- Protects admin routes with Basic Auth
- Verifies webhook calls using Twilio Signature Check

## 📁 Project Structure

```
.
├── app.py              # Main Flask app
├── requirements.txt    # Python dependencies
├── Dockerfile          # For containerized deployment
├── captain-definition  # CapRover deployment descriptor
├── .env.example        # Sample environment variables
├── .gitignore          # Files Git should ignore
```

## 🔧 Environment Variables

Create these in CapRover (App Configs → Environment Variables):

```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

WEBHOOK_USER=admin
WEBHOOK_PASS=changeme
```

## 📦 Installation & Deployment

### Run locally (for testing)
```bash
pip install -r requirements.txt
python app.py
```

### Deploy to CapRover
1. Create a new app (e.g. `whatsappbot`)
2. Upload code via CapRover UI or GitHub
3. Set environment variables
4. Enable HTTPS and deploy

## 🧪 Testing
1. Join Twilio Sandbox (via WhatsApp with keyword)
2. Send a message to your Twilio number
3. Watch the logs in CapRover → You should see incoming messages printed

## 🔐 Security Notes
- `/webhook` is open but secured with Twilio Signature Check
- All other routes are protected with Basic Auth

## 📝 License
MIT
