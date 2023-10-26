import sqlalchemy
from src import database as db

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

cart_id = 0

# class search_sort_options(str, Enum):
#     customer_name = "customer_name"
#     item_sku = "item_sku"
#     line_item_total = "line_item_total"
#     timestamp = "timestamp"

# class search_sort_order(str, Enum):
#     asc = "asc"
#     desc = "desc"   

# @router.get("/search/", tags=["search"])
# def search_orders(
#     customer_name: str = "",
#     potion_sku: str = "",
#     search_page: str = "",
#     sort_col: search_sort_options = search_sort_options.timestamp,
#     sort_order: search_sort_order = search_sort_order.desc,
# ):
#     """
#     Search for cart line items by customer name and/or potion sku.

#     Customer name and potion sku filter to orders that contain the 
#     string (case insensitive). If the filters aren't provided, no
#     filtering occurs on the respective search term.

#     Search page is a cursor for pagination. The response to this
#     search endpoint will return previous or next if there is a
#     previous or next page of results available. The token passed
#     in that search response can be passed in the next search request
#     as search page to get that page of results.

#     Sort col is which column to sort by and sort order is the direction
#     of the search. They default to searching by timestamp of the order
#     in descending order.

#     The response itself contains a previous and next page token (if
#     such pages exist) and the results as an array of line items. Each
#     line item contains the line item id (must be unique), item sku, 
#     customer name, line item total (in gold), and timestamp of the order.
#     Your results must be paginated, the max results you can return at any
#     time is 5 total line items.
#     """

#     return {
#         "previous": "",
#         "next": "",
#         "results": [
#             {
#                 "line_item_id": 1,
#                 "item_sku": "1 oblivion potion",
#                 "customer_name": "Scaramouche",
#                 "line_item_total": 50,
#                 "timestamp": "2021-01-01T00:00:00Z",
#             }
#         ],
#     }

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    name = new_cart.customer
    global cart_id 
    cart_id += 1

    # current_cart_id = SharedData.cart_id

    # create account
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
            """
            INSERT INTO accounts (customer_name) 
            VALUES (:name)
            """ 
            ), [{"name": name}]
        )

        # create cart just in case
        connection.execute(
            sqlalchemy.text(
            """
            INSERT INTO carts (cart_id, customer_name) 
            VALUES (:cart_id, :name)
            """, [{"cart_id":cart_id, "name": name}]
            )
        )

    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text("SELECT * FROM accounts WHERE id = :cart_id"), [{"cart_id": cart_id}])

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
                WHERE sku = :item_sku
                """
            ), [{"item_sku":item_sku}]).scalar()
        
        print(potion_id)
        
        available_potions = connection.execute(
            sqlalchemy.text(
                """
                SELECT SUM(change_quantity) FROM ledger_potions 
                WHERE potion_id = :potion_id
                """
            ), [{"potion_id":potion_id}]).scalar()
        
        # connection.execute(
        #     sqlalchemy.text(
        #         """
        #         INSERT INTO cart_items (cart_id, potion_id) 
        #         VALUES (:cart_id, :potion_id)
        #         """
        #     ), [{"cart_id":cart_id, "potion_id":potion_id}])
        
        if (item_quantity <= available_potions):
            connection.execute(
                sqlalchemy.text(
                    """UPDATE cart_items SET
                    quantity = :item_quantity
                    WHERE potion_id = :potion_id
                    """
                ), [{"item_quantity":item_quantity, "potion_id":potion_id}])
        else:
            raise HTTPException(status_code=400, message="Insufficient potions available in inventory to purchase. Try again.")

    return "OK"


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    print(cart_checkout)
    gold_earned = 0
    total_potions_bought = 0

    potion_dict = {}

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

            potion_sku = connection.execute(
                sqlalchemy.text(
                """
                SELECT sku FROM potions
                WHERE id = :potion_id
                """
                ), [{"potion_id":potion_id}]
                ).scalar()

            potion_quantity = potion[1]

            potion_dict[potion_sku] = potion_quantity

            price = connection.execute(
                sqlalchemy.text(
                """
                SELECT price FROM potions
                WHERE id = :potion_id
                """),[{"potion_id":potion_id}]
                ).scalar()
            
            total_potions_bought += potion_quantity
            gold_earned += price*potion_quantity
    

    with db.engine.begin() as connection:
        # Retrieve customer info (account_id)
        customer_name = connection.execute(
            sqlalchemy.text(
                """
                SELECT customer_name FROM carts
                WHERE cart_id = :cart_id
                )
                """
            ), [{"cart_id":cart_id}]
        ).scalar()

        account_id = connection.execute(
            sqlalchemy.text(
                """
                SELECT id FROM accounts
                WHERE customer_name = :customer_name
                """
            ), [{"customer_name":customer_name}]
        ).scalar()

        # Update transaction ledger
        description = ""

        for key,value in potion_dict.items():
            description += f"{key} bought : quantity of {value}, "

        # Write message to transactions ledger
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO account_transactions (description)
                VALUES (:description)
                """
            ), [{"description":description}]
        )

        # Get transaction id from row we just inserted
        transaction_id = connection.execute(
            sqlalchemy.text(
                """
                SELECT id FROM account_transactions 
                WHERE description = :description
                """
            ), [{"description":description}]
        )

        # Update ledger gold
        connection.execute(
            sqlalchemy.text(
            """
            INSERT INTO ledger_gold (account_id, transaction_id, change_gold)
            VALUES (:account_id, :transaction_id, :gold_earned)
            """
            ), [{"account_id":account_id, "transaction_id":transaction_id, "gold_earned":gold_earned}]
        )

        # Update ledger potions, subtract potions bought 
        for key,value in potion_dict.items():
            potion_id = connection.execute(
                sqlalchemy.text(
                """
                SELECT id FROM potions
                WHERE sku = key
                """
                ), [{"key":key}]
            ).scalar()

            connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO ledger_potions (account_id, transaction_id, potion_id, change_quantity)
                    VALUES (:account_id, :transaction_id, :potion_id, :change_quantity)
                    """
                ), [{"account_id":account_id, "transaction_id":transaction_id, 
                     "potion_id":potion_id, "change_quantity":-value}]
            )
            
        
    # with db.engine.begin() as connection:
    #     connection.execute(
    #         sqlalchemy.text(
    #             """
    #             UPDATE global_inventory SET
    #             gold = gold + :gold_earned
    #             """), [{"gold_earned":gold_earned}])
            
        
    # Update potions table, deduct potions that were sold 
    # with db.engine.begin() as connection:
    #     connection.execute(
    #         sqlalchemy.text(
    #             """
    #             UPDATE potions
    #             SET num_potions = potions.num_potions - cart_items.quantity
    #             FROM cart_items
    #             WHERE potion.id = cart_items.potion_id and cart_items.cart_id = :cart_id;
    #             """), [{"cart_id":cart_id}])

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": gold_earned}
