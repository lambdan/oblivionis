from fastapi import FastAPI
from playhouse.shortcuts import model_to_dict

from oblivionis.storage.storage_v2 import User

app = FastAPI()

@app.get("/users")
def list_users():
    users = [model_to_dict(user) for user in User.select()]
    return users

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = User.get_or_none(User.id == user_id)
    return model_to_dict(user) if user else {"error": "Not found"}