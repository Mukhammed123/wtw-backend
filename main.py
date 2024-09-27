from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from hashlib import sha256
import hmac
import time

app = FastAPI()

# Кросс-доменные запросы (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Разрешаем запросы с фронтенда
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище сессий (можно использовать что-то вроде Redis в будущем)
sessions = {}

# Функция проверки подлинности данных от Telegram
def verify_telegram_auth(data: dict, bot_token: str):
    check_hash = data.pop('hash')
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])
    secret_key = sha256(bot_token.encode()).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), sha256).hexdigest()

    if not hmac.compare_digest(hmac_hash, check_hash):
        raise HTTPException(status_code=403, detail="Invalid Telegram data")

# Эндпоинт авторизации через Telegram
@app.get("/auth")
async def auth(request: Request):
    data = dict(request.query_params)
    bot_token = "7719047280:AAEQ4XHAJEnMLy94ubgPkCgnq3-I11J-fYk"

    verify_telegram_auth(data, bot_token)

    # Сохраняем пользователя в сессии
    user_id = data['id']
    sessions[user_id] = {
        'first_name': data['first_name'],
        'balance': 1000,
    }

    return {"message": "Authorized", "user": sessions[user_id]}

# Эндпоинт для перевода средств
@app.post("/transfer")
async def transfer_funds(request: Request):
    body = await request.json()
    user_id = body.get("userId")
    recipient_id = body.get("recipientId")
    amount = body.get("amount")

    if not all([user_id, recipient_id, amount]):
        raise HTTPException(status_code=400, detail="Missing fields")

    if user_id not in sessions:
        raise HTTPException(status_code=404, detail="Sender not found")

    if recipient_id not in sessions:
        raise HTTPException(status_code=404, detail="Recipient not found")

    if sessions[user_id]['balance'] < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Обновляем баланс отправителя и получателя
    sessions[user_id]['balance'] -= amount
    sessions[recipient_id]['balance'] += amount

    return {"message": "Transfer successful"}

