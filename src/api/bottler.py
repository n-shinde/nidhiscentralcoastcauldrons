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

potion_id = 0

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """

    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0

    # Get description to add to account_transactions ledger
    description = ""
    potions_dict = {}

    with db.engine.begin() as connection:
        for potion in potions_delivered:
            this_potion_type = potion.potion_type
            potion_quantity = potion.quantity
            potion_id = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT id FROM potions
                    WHERE potion_type = :potion_type
                    """
                ), [{"potion_type":this_potion_type}]
            ).scalar()
            potion_sku = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT sku FROM potions
                    WHERE id = :potion_id
                    """
                ), [{"potion_id":potion_id}]
            ).scalar()

            potions_dict[potion_sku] = potion_quantity


    for key,value in potions_dict.items():
        description += f"{value} {key} potions acquired,  "


    # Write new transaction, get transaction id
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO account_transactions (description)
                VALUES (:description)
                """
            ), [{"description":description}]
        ).scalar()

        transaction_id = connection.execute(
            sqlalchemy.text(
                """
                SELECT id FROM account_transactions 
                WHERE description = :description
                """
            ), [{"description":description}]
        ).scalar()


    # Update potions and ledger_ml    
    with db.engine.begin() as connection:
        for potion in potions_delivered:

            # Update potions with new potions to add
            update_potion_type = potion.potion_type
            update_potion_quantity = potion.quantity
            update_potion_id = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT id FROM potions
                    WHERE potion_type = :potion_type
                    """
                ), [{"potion_type":update_potion_type}]
            ).scalar()


            # Update potions ledger with each new potion made
            connection.execute(
                sqlalchemy.text(
                """
                INSERT INTO ledger_potions (transaction_id, potion_id, quantity) 
                VALUES (:transaction_id, :potion_id, :quantity)
                """
            ), [{"transaction_id":transaction_id, "potion_id":update_potion_id, "quantity":update_potion_quantity}])


            # connection.execute(
            #     sqlalchemy.text(
            #     """
            #     UPDATE potions SET 
            #     num_potions = num_potions + :potion_quantity
            #     WHERE potion_type = :potion_type
            #     """
            # ), [{"potion_quantity":potion_quantity, "potion_type":potion_type}])

            # Track ml lost from making potions

            for i in range(0, len(this_potion_type)):
                if (i == 0 and this_potion_type[i] > 0):
                    red_ml -= this_potion_type[i]

                if (i == 1 and this_potion_type[i] > 0):
                    green_ml -= this_potion_type[i]
                

                if (i == 2 and this_potion_type[i] > 0):
                    blue_ml -= this_potion_type[i]
                

                if (i == 3 and this_potion_type[i] > 0):
                    dark_ml -= this_potion_type[i]
                    
            # end inner for loop
        # end potion loop
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ledger_ml (transaction_id, change_red_ml, change_green_ml, change_blue_ml, change_dark_ml)
                VALUES (:transaction_id, :red_ml, :green_ml, :blue_ml, :dark_ml)
                """
            ), [{"transaction_id":transaction_id, "red_ml":red_ml, "green_ml":green_ml, "blue_ml":blue_ml, "dark_ml":dark_ml}]
        )

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
        red_ml = connection.execute(sqlalchemy.text("SELECT SUM(change_red_ml) AS red_ml FROM ledger_ml")).scalar()
        green_ml = connection.execute(sqlalchemy.text("SELECT SUM(change_green_ml) AS green_ml FROM ledger_ml")).scalar()
        blue_ml = connection.execute(sqlalchemy.text("SELECT SUM(change_blue_ml) AS blue_ml FROM ledger_ml")).scalar()
        dark_ml = connection.execute(sqlalchemy.text("SELECT SUM(change_dark_ml) AS dark_ml FROM ledger_ml")).scalar()
    
        potions_to_make = connection.execute(sqlalchemy.text("SELECT potion_type FROM potions WHERE num_potions < 1")).all()
        potion_list = [item[0] for item in potions_to_make]


        print(potion_list)

    for potion_recipe in potion_list:
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

