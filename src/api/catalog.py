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
        potions = connection.execute(sqlalchemy.text(
            """
            SELECT sku, potion_type, num_potions, price FROM potions
            WHERE num_potions > 0
            """
        )).all()
    
    potion_list = []

    for potion in potions:
        potion_list.append(
            {"sku": potion[0],
             "name": potion[0]+ " mix",
             "quantity": potion[2],
             "price": potion[3],
             "potion_type": potion[1]}
        )
    
    return potion_list

