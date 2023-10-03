from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        num_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
        ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
        money = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))

    return {"number_of_potions": num_potions, "ml_in_barrels": ml, "gold": money}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
