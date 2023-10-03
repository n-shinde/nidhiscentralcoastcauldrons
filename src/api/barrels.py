import sqlalchemy
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)


class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int


@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """

    gold_spent = 0
    barrel_ml = 0

    for barrel in barrels_delivered:
        gold_spent += 50*(barrel.quantity)
        barrel_ml += barrel.ml_per_barrel

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - gold_spent"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + barrel_ml"))
        
    print(barrels_delivered)

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    num_barrels_bought = 0

    print(wholesale_catalog)

    with db.engine.begin() as connection:
        num_red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
        current_money = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
    
    # If number of red potions is less than 10, purchase a small red potion barrel
    if (num_red_potions < 10):
        for barrel in wholesale_catalog:
        # if barrel is small red potion type and we have money, then purchase 1
            if (barrel.sku == "SMALL_RED_BARREL" and current_money >= 50):
                with db.engine.begin() as connection:
                    num_barrels_bought += 1


    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": num_barrels_bought,
        }
    ]
