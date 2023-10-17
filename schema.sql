/* cart_items */
create table
  public.cart_items (
    cart_id integer generated by default as identity,
    potions_id integer not null,
    quantity integer not null default 0,
    constraint cart_items_pkey primary key (" cart_id"),
    constraint cart_items_ cart_id_fkey foreign key (" cart_id") references carts (cart_id) on update cascade on delete cascade,
    constraint cart_items_potions_id_fkey foreign key (potions_id) references potions (id) on update cascade on delete cascade
  ) tablespace pg_default;

/* carts */
create table
  public.carts (
    cart_id integer not null,
    customer_name text null,
    constraint carts_pkey primary key (cart_id)
  ) tablespace pg_default;

/* global_inventory */
create table
  public.global_inventory (
    id bigint generated by default as identity,
    created_at timestamp with time zone not null default now(),
    red_ml integer not null default 0,
    gold integer not null default 0,
    green_ml integer not null default 0,
    blue_ml integer not null default 0,
    dark_ml integer not null default 0,
    constraint global_inventory_pkey primary key (id),
    constraint global_inventory_id_key unique (id)
  ) tablespace pg_default;

/* potions */
create table
  public.potions (
    id integer generated by default as identity,
    created_at timestamp with time zone not null default now(),
    sku text not null default '""'::text,
    potion_type integer[] not null,
    num_potions integer not null default 0,
    price integer not null default 0,
    constraint potions_pkey primary key (id),
    constraint potions_sku_key unique (sku)
  ) tablespace pg_default;
