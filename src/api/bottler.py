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
        # checking first if potion is red and then retrieving quantity
        if potion.potion_type == [100, 0, 0, 0]:
            total_quantity_delivered += potion.quantity
            total_red_ml += 100*potion.quantity
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET num_red_potions = num_red_potions + total_quantity_delivered"))
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET num_red_ml = num_red_ml - total_red_ml"))

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

    # Initial logic: bottle all barrels into red potions.

    with db.engine.begin() as connection:
        barrel_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
                                           
    # return the number of bottles that we want to deliver
    bottles_to_deliver = barrel_ml // 100


    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": bottles_to_deliver,
            }
    ]
