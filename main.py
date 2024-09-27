# main.py
from fastapi import FastAPI, Request, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from database import get_db, User
from sqlalchemy.exc import IntegrityError

app = FastAPI()


@app.post("/users")
async def auth(payload: dict = Body(...), db: Session = Depends(get_db)):
    tg_data = payload

    # Extract relevant user info
    telegram_id = tg_data.get("id")
    first_name = tg_data.get("first_name")
    last_name = tg_data.get("last_name")
    username = tg_data.get("username")

    # Save the user information to the database
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
        # Handle the case where the username already exists
        return {"status": "error", "message": "Username already exists.", "user": None}

    return {"status": "success", "user": {
        "telegram_id": new_user.telegram_id,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "username": new_user.username,
        "balance": new_user.balance
    }}


@app.get("/users")
async def get_users(telegram_id: str = Query(None), db: Session = Depends(get_db)):
    if telegram_id:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            return {"status": "success", "user": {
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "balance": user.balance
            }}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        users = db.query(User).all()
        return {
            "status": "success",
            "users": [
                {
                    "telegram_id": user.telegram_id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "balance": user.balance
                } for user in users
            ]
        }


@app.post("/transfer")
async def transfer(transfer_data: dict = Body(...), db: Session = Depends(get_db)):
    sender_id = transfer_data.get("sender_id")
    receiver_id = transfer_data.get("receiver_id")
    amount = transfer_data.get("amount")

    # Validate the amount
    if amount <= 0:
        raise HTTPException(
            status_code=400, detail="Amount must be greater than zero")

    # Fetch sender and receiver from the database
    sender = db.query(User).filter(User.telegram_id == sender_id).first()
    receiver = db.query(User).filter(User.telegram_id == receiver_id).first()

    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")

    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    if sender.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Perform the transfer
    sender.balance -= amount
    receiver.balance += amount

    db.commit()

    return {
        "status": "success",
        "sender_balance": sender.balance,
        "receiver_balance": receiver.balance
    }
