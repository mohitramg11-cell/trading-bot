import requests

TOKEN = "8550191978:AAEo2HeVwMBU9C4k0ZpT6j0K5SK4bXXg0NU"
CHAT_ID = "1160483967"

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

send("🔥 BOT WORKING SUCCESS 🔥")
