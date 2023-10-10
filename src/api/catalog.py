from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.

    with db.engine.begin() as connection:
        num_red_potions_to_sell = connection.execute(sqlalchemy.text(
            "SELECT num_red_potions FROM global_inventory"))
        num_green_potions_to_sell = connection.execute(sqlalchemy.text(
            "SELECT num_green_potions FROM global_inventory"))
        num_blue_potions_to_sell = connection.execute(sqlalchemy.text(
            "SELECT num_blue_potions FROM global_inventory"))


    return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": num_red_potions_to_sell,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            },
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": num_green_potions_to_sell,
                "price": 10,
                "potion_type": [0, 100, 0, 0],
            },
            {
                "sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity": num_blue_potions_to_sell,
                "price": 10,
                "potion_type": [0, 0, 100, 0],
            }
        ]
