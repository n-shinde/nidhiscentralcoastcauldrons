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

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    global cart_id 
    cart_id += 1

    name = new_cart.customer
    customer_id = cart_id

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("INSERT INTO carts (cart_id, customer_name) VALUES (:customer_id, :name)"), 
                           [{"customer_id": customer_id, "name": name}])

    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text("SELECT * FROM carts WHERE cart_id = :cart_id"), [{"cart_id": cart_id}])

    return {cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    available_potions = 0
    potion_id = 0
    item_quantity = cart_item.quantity

    with db.engine.begin() as connection:
        potion_id = connection.execute(
            sqlalchemy.text(
                """
                SELECT id FROM potions 
                WHERE sku == :item_sku
                """
            ), [{"item_sku":item_sku}])
        
        available_potions = connection.execute(
            sqlalchemy.text(
                """
                SELECT num_potions FROM potions 
                WHERE sku == :item_sku
                """
            ), [{"item_sku":item_sku}])
        
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO cart_items (cart_id, potion_id) 
                VALUES (:cart_id, :potion_id)
                """
            ), [{"cart_id":cart_id, "potion_id":potion_id}])
        
        if (item_quantity <= available_potions):
            connection.execute(
                sqlalchemy.text(
                    """UPDATE cart_items SET
                    quantity = :cart_item.quantity
                    WHERE potion_id = :potion_id
                    """
                ), [{"cart_item.quantity":cart_item.quantity, "potion_id":potion_id}])
        else:
            raise HTTPException(status_code=400, message="Insufficient potions available in inventory to purchase. Try again.")

    return "OK"


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    gold_earned = 0
    total_potions_bought = 0

    # Calculate gold earned 
    with db.engine.begin() as connection:
        valid_potions = connection.execute(
            sqlalchemy.text(
                """
                SELECT potion_id, quantity FROM cart_items
                WHERE cart_id = :cart_id and cart_id.quantity > 0
                """
            ), [{"cart_id":cart_id}]).all()
        
        for potion in valid_potions:
            potion_id = potion[0]
            price = connection.execute(
                sqlalchemy.text(
                """
                SELECT price FROM potions
                WHERE id = :potion_id
                """),[{"potion_id":potion_id}] ).scalar()
            total_potions_bought += potion[1]
            gold_earned += price*potion[1]
    
    # Update global inventory with money earned
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET
                gold = gold + :gold_earned
                """))
            
        
    # Update potions table, deduct potions that were sold 
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE potions
                SET num_potions = potions.num_potions - cart_items.quantity
                FROM cart_items
                WHERE potion.id = cart_items.potion_id and cart_items.cart_id = :cart_id;
                """))

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": gold_earned}
