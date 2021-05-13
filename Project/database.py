import argparse
import os.path
import typing
from configparser import ConfigParser
import functools

import pandas
import sqlalchemy
from typing import Dict


INSERT = "insert into customer(name, age) values (:name, :age)"
SELECT = "select * from customer"
URL = '{driver}://{user}:{password}@{host}:{port}/{database}'

INSERT_FOOD = """insert into food(id, description, data_type, publication_date, food_code)
 values(:fdcId, :description, :data_type, :publication_date, :food_code)"""
INSERT_INGREDIENTS = """insert into ingredients(id, name, unit_name) values(:id, :name, :unit_name)"""
INSERT_FOOD_INGREDIENTS = """insert into food_ingredients(food_id, ingredients_id, amount) values(:food_id, :ingredients_id, :amount)"""
INDEXES = """
create index on food_nutrient (fdc_id);
create index on food ((lower(description)));"""

DATABASE_INI = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs', 'database.ini')


def config(db_config: str,
           section: str = 'postgresql') -> Dict[str, str]:
    """
    Get a config dictionary from a parsed .ini file
    :param db_config: path to the config file
    :param section: section that contains the db connection information
    :return: Dict[str, str]
    """
    parser = ConfigParser()
    parser.read(db_config)
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in {db_config}')
    return db


def parse_food_results(results, ingredient_map):
    if not results:
        return pandas.DataFrame(), pandas.DataFrame()
    foods = []

    ingredients_list = []
    for food in results:
        for ingredient in food['foodNutrients']:
            ingredient_map[ingredient['number']] = {'id': ingredient['number'], 'name': ingredient['name'], 'unit_name': ingredient['unitName']}
            ingredients_list.append({'food_id': food['fdcId'], 'ingredient_id': ingredient['number'], 'amount': ingredient['amount'] if ingredient['amount'] else 0})
        food.pop('foodNutrients')
        if food.get('ndbNumber'):
            food.pop('ndbNumber')
        foods.append(food)
    foods_df = pandas.DataFrame(foods)
    foods_df.rename(columns={'fdcId': 'id', 'dataType': 'data_type', 'publicationDate': 'publication_date', 'foodCode': 'food_code'}, inplace=True)

    ingredients_df = pandas.DataFrame(ingredients_list)
    return foods_df, ingredients_df


def save_df_csv(foods_df, ingredients_df, ingredient_list, pn):
    foods_df.to_csv('/Users/nathaniel/food/food{id}.csv'.format(id=pn))
    ingredients_df.to_csv('/Users/nathaniel/food/ingreds{id}.csv'.format(id=pn))
    pandas.DataFrame(ingredient_list).to_csv('/Users/nathaniel/food/ing_list{id}.csv'.format(id=pn))


def get_connection(db_config: str) -> sqlalchemy.engine.base.Engine:
    """
    Create a sqlalchemy engine from a dictionary of config parameters
    :param db_config:
    :return: Sqlalchemy Engine
    """
    params = config(db_config=db_config)
    conn = sqlalchemy.create_engine(URL.format(**params))
    return conn


# create table saved_nutrients (name text, nutrient_id numeric);
def get_user_nutrients(user: str) -> typing.List:
    conn = get_connection(db_config=DATABASE_INI)
    select = "select nutrient_id from saved_nutrients where name=:user"
    return pandas.read_sql(sqlalchemy.text(select), conn, params={'user': user}).nutrient_id.unique()


def save_user_nutrient(user: str, nutrient_id: int):
    conn = get_connection(db_config=DATABASE_INI)
    insert = "insert into saved_nutrients(name, nutrient_id) values(:name, :nutrient_id)"
    conn.execute(sqlalchemy.text(insert), {'name': user, 'nutrient_id': nutrient_id})


def get_nutrient_names(nutrient_ids: typing.List):
    if len(nutrient_ids) == 0:
        return {}
    conn = get_connection(db_config=DATABASE_INI)
    select = "select name, nutrient_nbr from nutrient where nutrient_nbr IN :I"
    return pandas.read_sql(sqlalchemy.text(select), conn, params={'I': tuple(nutrient_ids)}).set_index('nutrient_nbr').to_dict()['name']


def pull_bubble_graph_data():
    db_engine = get_connection(db_config=DATABASE_INI)
    select = 'select LEFT(n.name, 1) as lbl, n.name, n.unit_name, count(*) ' \
             'from food_nutrient fn, nutrient n where n.id = fn.nutrient_id ' \
             'group by LEFT(n.name, 1), n.name, n.unit_name;'
    return pandas.read_sql(sqlalchemy.text(select), db_engine)


def pull_pie_chart_data(fdc_id):
    db_engine = get_connection(db_config=DATABASE_INI)
    select = ('select n.name, nf.amount from food f join food_nutrient nf on (f.fdc_id = nf.fdc_id) '
              'join nutrient n on (nf.nutrient_id = n.nutrient_nbr) WHERE f.fdc_id = {} group by n.name, nf.amount;'.format(str(fdc_id)))
    return pandas.read_sql(sqlalchemy.text(select), db_engine)


def pull_food_by_description(description, exclude_ids):
    db_engine = get_connection(db_config=DATABASE_INI)
    select = 'select * from food where lower(description) like :search limit 20'
    if exclude_ids:
        select = 'select fd.*, fn.nutrient_id from (select * from food where lower(description) ' \
                 'like :search) as fd join food_nutrient as fn on (fd.fdc_id = fn.fdc_id);'
    return pandas.read_sql(sqlalchemy.text(select), db_engine, params={'search': '%'+description.lower()+'%'})


def pull_nutrients_by_name(nutrient_term):
    db_engine = get_connection(db_config=DATABASE_INI)
    select = 'select id, name, unit_name, nutrient_nbr, rank from nutrient where lower(name) like :search limit 20'
    return pandas.read_sql(sqlalchemy.text(select), db_engine, params={'search': '%'+nutrient_term.lower()+'%'})


def load_csv(engine, csv_path):
    food_df = pandas.read_csv(os.path.join(csv_path, "food.csv"))
    food_df.to_sql("food", engine, if_exists='replace')
    nutrient_df = pandas.read_csv(os.path.join(csv_path, "nutrient.csv"))
    nutrient_df.to_sql("nutrient", engine, if_exists='replace')
    food_nutrient_df = pandas.read_csv(os.path.join(csv_path, "food_nutrient.csv"), low_memory=False)
    print('Loading db')
    food_nutrient_df.to_sql('food_nutrient', engine, if_exists='replace', chunksize=5000)
    conn = get_connection(db_config=DATABASE_INI)
    conn.execute(INDEXES)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv-data-path', required=True)
    args = parser.parse_args()
    load_csv(get_connection(db_config=DATABASE_INI), args.csv_data_path)
    #load_csv("food_nutrient", db_engine, "/Users/nathaniel/food/FULLDATA/food_nutrient.csv")
    #nutrient_df = load_csv("nutrient", db_engine, "/Users/nathaniel/food/FULLDATA/nutrient.csv")

