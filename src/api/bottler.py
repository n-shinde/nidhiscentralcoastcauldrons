from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """

    # modify the database to reduce the number of ml we have and increase
    # num potions

    for potion in potions_delivered:
        if potion.potion_type == [100, 0, 0, 0]:
            total_red_potions += potion.quantity
            total_red_ml += 100*potion.quantity
        
        if potion.potion_type == [0, 100, 0, 0]:
            total_green_potions += potion.quantity
            total_green_ml += 100*potion.quantity
        
        if potion.potion_type == [0, 0, 100, 0]:
            total_blue_potions += potion.quantity
            total_blue_ml += 100*potion.quantity

    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET num_red_potions = num_red_potions + total_red_potions"))
        connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET num_green_potions = num_green_potions + total_green_potions"))
        connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET num_blue_potions = num_blue_potions + total_blue_potions"))
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET num_red_ml = num_red_ml - total_red_ml"))
        connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET num_green_ml = num_green_ml - total_green_ml"))
        connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET num_blue_ml = num_blue_ml - total_blue_ml"))

    print(potions_delivered)

    return "OK"


# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels (red, green, blue) into their respective potions.

    with db.engine.begin() as connection:
        red_barrel_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
        green_barrel_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        blue_barrel_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory"))
                                           
    # return the number of bottles that we want to deliver
    red_bottles_to_deliver = red_barrel_ml // 100
    green_bottles_to_deliver = green_barrel_ml // 100
    blue_bottles_to_deliver = blue_barrel_ml // 100


    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": red_bottles_to_deliver,
            },
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": green_bottles_to_deliver,
            },
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": blue_bottles_to_deliver,
            }
    ]
