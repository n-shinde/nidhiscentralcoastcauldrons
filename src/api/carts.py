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
    carts[cart_id].update({"item":item_sku, "quantity":cart_item.quantity})

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    potions_bought = 0
    gold_earned = 0

    with db.engine.begin() as connection:
        potions_for_sale = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))

    if (carts[cart_id]["item"] == "RED_POTION_0"):
        if (carts[cart_id]["quantity"] >= potions_for_sale):
            potions_bought = carts[cart_id]["quantity"]
            gold_earned = potions_bought*50
        else:
            raise HTTPException(status_code=400, message="Items in cart not available.")


    #update database
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold + gold_earned"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions - potions_bought"))

    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_earned}

