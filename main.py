# main.py
from fastapi import FastAPI, Request, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from database import get_db, User
from sqlalchemy.exc import IntegrityError
from utils import get_users_response

app = FastAPI(
    docs_url="/test/docs",
    redoc_url="/test/redoc",
    openapi_url="/test/openapi.json"
)


@app.post("/test/users")
async def auth(payload: dict = Body(...), db: Session = Depends(get_db)):
    tg_data = payload

    telegram_id = tg_data.get("id")
    first_name = tg_data.get("first_name")
    last_name = tg_data.get("last_name")
    username = tg_data.get("username")

    new_user = User(
        telegram_id=telegram_id,
        first_name=first_name,
        last_name=last_name,
        username=username
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        return {"status": "error", "message": "Username already exists.", "user": None}

    return {"status": "success", "user": get_users_response(new_user)}


@app.get("/test/users")
async def get_users(telegram_id: str = Query(None), db: Session = Depends(get_db)):
    query = db.query(User)

    if telegram_id:
        user = query.filter(User.telegram_id == telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "success", "user": get_users_response(user)}

    users = query.all()
    return {
        "status": "success",
        "users": [get_users_response(user) for user in users]
    }


@app.post("/test/transfer")
async def transfer(transfer_data: dict = Body(...), db: Session = Depends(get_db)):
    sender_id = transfer_data.get("sender_id")
    receiver_id = transfer_data.get("receiver_id")
    amount = transfer_data.get("amount")

    if amount <= 0:
        raise HTTPException(
            status_code=400, detail="Amount must be greater than zero")

    sender = db.query(User).filter(User.telegram_id == sender_id).first()
    receiver = db.query(User).filter(User.telegram_id == receiver_id).first()

    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")

    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    if sender.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    sender.balance -= amount
    receiver.balance += amount

    db.commit()

    return {
        "status": "success",
        "sender_balance": sender.balance,
        "receiver_balance": receiver.balance
    }
