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
    total_potions = 0
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0
    total_ml = 0
    gold = 0

    with db.engine.begin() as connection:
        red_ml = connection.execute(sqlalchemy.text("SELECT SUM(change_red_ml) AS red_ml FROM ledger_ml")).scalar()
        green_ml = connection.execute(sqlalchemy.text("SELECT SUM(change_green_ml) AS green_ml FROM ledger_ml")).scalar()
        blue_ml = connection.execute(sqlalchemy.text("SELECT SUM(change_blue_ml) AS blue_ml FROM ledger_ml")).scalar()
        dark_ml = connection.execute(sqlalchemy.text("SELECT SUM(change_dark_ml) AS dark_ml FROM ledger_ml")).scalar()

        total_potions = connection.execute(sqlalchemy.text("SELECT SUM(change_quantity) FROM ledger_potions")).scalar()
        
        gold = connection.execute(sqlalchemy.text("SELECT SUM(change_gold) AS gold FROM ledger_gold")).scalar()
    
    total_ml = red_ml + green_ml + blue_ml + dark_ml

    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": gold}

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
