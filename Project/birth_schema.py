import sqlalchemy

FOOD_TABLE = """
create table food(
id integer,
description text,
data_type text,
publication_date date,
food_code integer);"""

FOOD_NUTRIENT_TABLE = """ 
create table food_nutrient(
id numeric,
name text,
unit_name text);"""

NUTRIENT_TABLE = """ 
create table nutrient(
food_id integer,
ingredient_id numeric,
amount numeric);"""

DROP_TABLES = """
drop table food;
drop table food_nutrient;
drop table nutrient;
"""


def birth_schema(engine: sqlalchemy.engine.base.Engine, drop_table):
    if drop_table:
        engine.execute(DROP_TABLES)
    engine.execute(FOOD_TABLE)
    engine.execute(FOOD_NUTRIENT_TABLE)
    engine.execute(NUTRIENT_TABLE)
