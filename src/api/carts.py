from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


cart_id = 0
carts = {}
item_list = []
quantity_list = []

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    # ask what the cart_id
    cart_id += 1
    carts[cart_id] = {"customer_name":new_cart.customer}
    return {"cart_id": str(cart_id)}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    return {carts[cart_id]}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    item_list.append(item_sku)
    quantity_list.append(cart_item.quantity)
    carts[cart_id].update({"item":item_list, "quantity":quantity_list})

    return "OK"


class CartCheckout(BaseModel):
    payment: str

# What does cart_checkout do??? Has payment variable but do i do anything with it?
@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    red_potions_bought, green_potions_bought, blue_potions_bought = 0
    gold_earned = 0

    with db.engine.begin() as connection:
        red_potions_for_sale = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
        green_potions_for_sale = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        blue_potions_for_sale = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory"))
    
    for item_sku, quantity in zip(carts[cart_id]["item"],carts[cart_id]["quantity"]):
        # red potions
        if (item_sku == "RED_POTION_0"):
            if (quantity >= red_potions_for_sale and quantity != 0):
                red_potions_bought = quantity
                gold_earned += red_potions_bought*50
            else:
                raise HTTPException(status_code=400, message="Items in cart not available.")
        # green potions
        if (item_sku == "GREEN_POTION_0"):
            if (quantity >= green_potions_for_sale and quantity != 0):
                green_potions_bought = quantity
                gold_earned += red_potions_bought*10
            else:
                raise HTTPException(status_code=400, message="Items in cart not available.")
        # blue potions
        if (item_sku == "BLUE_POTION_0"):
            if (quantity >= blue_potions_for_sale and quantity != 0):
                blue_potions_bought = quantity
                gold_earned += red_potions_bought*10
            else:
                raise HTTPException(status_code=400, message="Items in cart not available.")


    #update database
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold + gold_earned"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions - potions_bought"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions - potions_bought"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = num_blue_potions - potions_bought"))

    total_potions_bought = red_potions_bought + blue_potions_bought + green_potions_bought

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": gold_earned}

