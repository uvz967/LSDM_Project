import pandas
import requests
import sqlalchemy

from database import parse_food_results, save_df_csv

FDA_LIST = 'https://api.nal.usda.gov/fdc/v1/foods/list?pageSize=200&pageNumber={pn}&api_key=v8DwCqm78EULEKCJlm2yEikabWag4hfLVA64Hb1d'

FDA_ITEM = 'https://api.nal.usda.gov/fdc/v1/food/1624897?api_key=v8DwCqm78EULEKCJlm2yEikabWag4hfLVA64Hb1d'


def get_food_data_list(engine: sqlalchemy.engine.base.Engine):
    ingredient_map = {}
    for pn in range(20):
        print(f"Pulling {pn*200}")
        resp = requests.get(FDA_LIST.format(pn=pn))
        if resp:
            results = resp.json()
            foods_df, ingredients_df = parse_food_results(results, ingredient_map)
            if foods_df.empty:
                break
            foods_df.to_sql('food', engine, if_exists='append', index=False)
            ingredients_df.to_sql('food_ingredients',  engine, if_exists='append', index=False)
            save_df_csv(foods_df, ingredients_df, list(ingredient_map.values()), pn)
        else:
            print(resp)
            break
    ingredient_df = pandas.DataFrame(list(ingredient_map.values()))
    ingredient_df.to_sql('ingredients', engine, if_exists='append', index=False)


def get_food_detail():
    resp = requests.get(FDA_ITEM)
    if resp:
        res = resp.json()
        print(res)
    else:
        print(resp)


if __name__ == '__main__':
    get_food_detail()
