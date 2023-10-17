from fastapi import APIRouter, Depends, HTTPException
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

    # First update potions with new potions made
    
    with db.engine.begin() as connection:
        for potion in potions_delivered:

            # Update potions with new potions to add
            potion_type = potion.potion_type
            potion_quantity = potion.quantity

            connection.execute(
                sqlalchemy.text(
                """
                UPDATE potions SET 
                num_potions = num_potions + :potion_quantity
                WHERE potion_type = :potion_type
                """
            ), [{"potion_quantity":potion_quantity, "potion_type":potion_type}])

            # Deduct ml from inventory
            for i in range(0, len(potion_type)):
                if (i == 0 and potion_type[i] > 0):
                    new_red = potion_type[i]
                    connection.execute(
                        sqlalchemy.text(
                        """
                        UPDATE global_inventory SET 
                        red_ml = red_ml - :new_red
                        """
                    ), [{"new_red":new_red}])

                if (i == 1 and potion_type[i] > 0):
                    new_green = potion_type[i]
                    connection.execute(
                        sqlalchemy.text(
                        """
                        UPDATE global_inventory SET 
                        green_ml = green_ml - :new_green
                        """
                    ), [{"new_green":new_green}])

                if (i == 2 and potion_type[i] > 0):
                    new_blue = potion_type[i]
                    connection.execute(
                        sqlalchemy.text(
                        """
                        UPDATE global_inventory SET 
                        blue_ml = blue_ml - :new_blue
                        """
                    ), [{"new_blue":new_blue}])

                if (i == 3 and potion_type[i] > 0):
                    new_dark = potion_type[i]
                    connection.execute(
                        sqlalchemy.text(
                        """
                        UPDATE global_inventory SET 
                        dark_ml = dark_ml - :new_dark
                        """
                    ), [{"new_dark":new_dark}])
            # end inner for loop
        # end potion loop

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

    bottle_list = []

    with db.engine.begin() as connection:
        red_ml = connection.execute(sqlalchemy.text("SELECT red_ml FROM global_inventory")).scalar()
        green_ml = connection.execute(sqlalchemy.text("SELECT green_ml FROM global_inventory")).scalar()
        blue_ml = connection.execute(sqlalchemy.text("SELECT blue_ml FROM global_inventory")).scalar()
        dark_ml = connection.execute(sqlalchemy.text("SELECT dark_ml FROM global_inventory")).scalar()
    
        potions_to_make = connection.execute(sqlalchemy.text("SELECT potion_type FROM potions WHERE num_potions < 1")).all()

        print(potions_to_make)

    for potion_recipe in potions_to_make:
        r = potion_recipe[0] 
        print(r)
        g = potion_recipe[1]
        print(g)
        b = potion_recipe[2]
        d = potion_recipe[3]
        
        if (red_ml >= r and green_ml >= g and blue_ml >= b and dark_ml >= d):
            bottle_list.append(
                {
                    "potion_type": potion_recipe,
                    "quantity": 1
                }
            )
            if (r > 0):
                red_ml -= r
            if (g > 0):
                green_ml -= g
            if (b > 0):
                blue_ml -= b
            if (d > 0):
                dark_ml -= d
            
    return bottle_list

