import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
from src import database as db
import SharedData

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
    red_ml = 0
    blue_ml = 0
    green_ml = 0
    dark_ml = 0

    barrel_dict = {}

    SharedData.barrel_id += 1
    print(SharedData.barrel_id)

    SharedData.gold_id += 1
    print(SharedData.gold_id)


    for barrel in barrels_delivered:
        gold_spent += barrel.price * barrel.quantity
        barrel_dict[barrel.sku] = barrel.quantity

        # red barrel
        if barrel.potion_type == [1, 0, 0, 0]:
            red_ml += barrel.ml_per_barrel * barrel.quantity
        # green barrel
        elif barrel.potion_type == [0, 1, 0, 0]:
            green_ml += barrel.ml_per_barrel * barrel.quantity
        # blue barrel
        elif barrel.potion_type == [0, 0, 1, 0]:
            blue_ml += barrel.ml_per_barrel * barrel.quantity
        # dark barrel
        elif barrel.potion_type == [0, 0, 0, 1]:
            dark_ml += barrel.ml_per_barrel * barrel.quantity
        else:
            raise HTTPException(status_code=400, message="Bad request. Barrel type invalid.")
    
    gold_spent = -gold_spent
    

    print(f"gold_spent: {gold_spent}, red_ml: {red_ml}, green_ml: {green_ml}, blue_ml: {blue_ml}, dark_ml: {dark_ml}")

    # Update ledger ml
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ledger_ml (transaction_id, change_red_ml, change_green_ml, change_blue_ml, change_dark_ml)
                VALUES (:barrel_id, :red_ml, :green_ml, :blue_ml, :dark_ml)
                """
            ), [{"barrel_id":SharedData.barrel_id, "red_ml":red_ml, "green_ml":green_ml, "blue_ml":blue_ml, "dark_ml":dark_ml}]
        )
    # Update ledger gold
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ledger_gold (transaction_id, change_gold)
                VALUES (:gold_id, :gold_spent)
                """
            ), [{"id":SharedData.gold_id, "gold_spent":gold_spent}]
        )
    
    description = ""
    for key,value in barrel_dict.items():
        description += f"{key} barrel : quantity of {value}, "

    # Write message to transactions ledger
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO account_transactions (description)
                VALUES (:description)
                """
            ), [{"description":description}]
        )



    # with db.engine.begin() as connection:
    #     connection.execute(
    #         sqlalchemy.text(
    #             """
    #             UPDATE global_inventory SET
    #             gold = gold - :gold_spent,
    #             red_ml = red_ml + :red_ml,
    #             green_ml = green_ml + :green_ml,
    #             blue_ml = blue_ml + :blue_ml,
    #             dark_ml = dark_ml + :dark_ml
    #             """), [{"gold_spent":gold_spent, "red_ml":red_ml, 
    #                     "green_ml":green_ml, "blue_ml":blue_ml, "dark_ml":dark_ml}])


    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    barrel_list = []

    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT SUM(change_gold) AS gold FROM ledger_gold")).scalar()

    print(wholesale_catalog)

    while (gold > 60):
        for barrel in wholesale_catalog:
            if (gold >= barrel.price*barrel.quantity):
                gold -= barrel.price*barrel.quantity
                barrel_list.append({
                    "sku": barrel.sku,
                    "quantity": barrel.quantity
                })
        
    # for barrel in wholesale_catalog:
    #     if (gold >= barrel.price*barrel.quantity):
    #         gold -= barrel.price*barrel.quantity
    #         barrel_list.append({
    #             "sku": barrel.sku,
    #             "quantity": barrel.quantity
    #         })

    return barrel_list
