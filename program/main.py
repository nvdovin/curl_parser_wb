import requests
import json
from transcrypter import transcription
import sqlite3
import os

from urllib.parse import urlencode

class WBParser:
    def __init__(self, response: str, TG_ID=0) -> None:
        self.response = response
        self.TG_ID = TG_ID


    def get_json_file(self, page):
        """Данная функция предназначена для того, чтобы получать json файл, подключаясь к api сайта.

        Args:
            response (str): _description_
            page (int, optional): _description_. Defaults to 1.
        """
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Origin': 'https://www.wildberries.ru',
            'Referer': f'https://www.wildberries.ru/catalog/0/search.aspx?page={page}&sort=popular&{urlencode({"search": self.response})}',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        response = requests.get(
            f'https://search.wb.ru/exactmatch/ru/common/v4/search?TestGroup=control&TestID=286&appType=1&curr=rub&dest=-1257786&page={page}&{urlencode({"query": self.response})}&regions=80,38,83,4,64,33,68,70,30,40,86,75,69,1,31,66,110,48,22,71,114&resultset=catalog&sort=popular&spp=32&suppressSpellcheck=false',
            headers=headers,
        )
        return response.json()


    def parse_ready_json(self):
        try:
            for page in range(1, 11):
                print(f"Парсинг страницы: {page}")
                data_list = self.get_json_file(page)["data"]["products"]
                for product in data_list:
                    product_url = f"https://www.wildberries.ru/catalog/{product['id']}/detail.aspx"
                    produce_name = product["name"]
                    brand = product["brand"]

                    try:
                        price = self.get_price(product["salePriceU"])
                    except:
                        print(f"По ссылке {product_url} \nне нашел цены")
                        price = 0
                    product_id = product["id"]

                    table_name = transcription(self.response)
                    if not os.path.exists("databases"):
                        os.mkdir("databases")
                    con = sqlite3.connect(f"databases/User_{self.TG_ID}.db")
                    cur = con.cursor()

                    cur.execute(f"""--sql
                                CREATE TABLE IF NOT EXISTS {table_name}(
                                product_id VARCHAR(10),
                                product_name VARCHAR(20),
                                brand VARCHAR(10),
                                current_price FLOAT,
                                pevious_price FLOAT NULL,
                                url_link VARCHAR(50)
                                )                    
                                """)

                    already_used = cur.execute(f"""--sql
                                                SELECT url_link FROM {table_name}
                                                """)


                    if product_url not in str(already_used.fetchall()):
                        cur.execute(f"""--sql
                                    INSERT INTO {table_name}(
                                    product_id,
                                    product_name, 
                                    brand,
                                    current_price, 
                                    url_link)
                                    VALUES(
                                    '{product_id}',
                                    '{produce_name}', 
                                    '{brand.replace("'", "")}',
                                    {price}, 
                                    '{product_url}'
                                    )
                                    """)
                    else:
                        cur.execute(f"""--sql
                                    UPDATE {table_name}
                                    SET
                                    pevious_price=current_price,
                                    current_price={price}
                                    WHERE url_link='{product_url}'
                                    """)
                    con.commit()

            if not os.path.exists("request_data"):
                os.mkdir("request_data")

            if not os.path.isfile(f"request_data/User_{self.TG_ID}.json"):
                with open(f"request_data/User_{self.TG_ID}.json", "w", encoding="utf=8") as json_file:
                    json.dump(
                        {f"{table_name}": f"{self.response}"},
                        json_file,
                        ensure_ascii=False,
                        indent=4
                    )
            else:
                with open(f"request_data/User_{self.TG_ID}.json", "r", encoding="utf=8") as json_file:
                    data_from_json = json.load(json_file)
                    data_from_json[f"{table_name}"] = f"{self.response}"
                    print(data_from_json)
                    with open(f"request_data/User_{self.TG_ID}.json", "w", encoding="utf=8") as json_file:
                        json.dump(
                            data_from_json,
                            json_file,
                            ensure_ascii=False,
                            indent=4
                        )

        except Exception as _error:
            print(_error)
            pass


    def reparse_pages(self, id):
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Origin': 'https://www.wildberries.ru',
            'Referer': f'https://www.wildberries.ru/catalog/{id}/detail.aspx',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        response = requests.get(
            f'https://card.wb.ru/cards/detail?appType=1&curr=rub&dest=-1257786&regions=80,38,83,4,64,33,68,70,30,40,86,75,69,1,31,66,110,48,22,71,114&spp=31&nm={id}',
            headers=headers,
        )
        

    @staticmethod
    def get_price(price: str):
        str_price = str(price)
        return "".join(list(str_price)[:-2])


def main():
    response = input("Ваш запрос: ")
    wb = WBParser(response=response)
    wb.parse_ready_json()


def main_cycle():
    chose = input('''Выбери тип действия
new - новый запрос.
refr - обновить старый
sw - показать таблицу
q - выход ''')
    match chose:
        case "new":
            pass
        
        case "refr":
            pass
        
        case "sw":
            pass
        
        case "q":
            pass
        
    main()