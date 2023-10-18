import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException
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
    red_ml = 0
    blue_ml = 0
    green_ml = 0
    dark_ml = 0


    for barrel in barrels_delivered:
        gold_spent += barrel.price * barrel.quantity

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
    

    print(f"gold_spent: {gold_spent}, red_ml: {red_ml}, green_ml: {green_ml}, blue_ml: {blue_ml}, dark_ml: {dark_ml}")


    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET
                gold = gold - :gold_spent
                red_ml = red_ml + :red_ml
                green_ml = green_ml + :green_ml
                blue_ml = blue_ml + :blue_ml
                dark_ml = dark_ml + :dark_ml
                """), [{"gold_spent":gold_spent, "red_ml":red_ml, 
                        "green_ml":green_ml, "blue_ml":blue_ml, "dark_ml":dark_ml}])


    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    barrel_list = []

    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()

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
