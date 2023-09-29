import requests
import json
from transcrypter import transcription
import sqlite3
import os
from datetime import datetime

from urllib.parse import urlencode

class WBParser:
    def __init__(self, response: str, TG_ID=0, new_request=False) -> None:
        """### Класс для создания новых запросов, обновления старых, просмотра готовых запросов

        #### Args:
            - response (str): Запрос, с которым мы идём на сайт.
            - TG_ID (int, optional): ID пользователя телеграм. Defaults to 0.
            - new_request (bool, optional): Флаг, который отвечает за записнь нового запроса в лист запросов. Defaults to False
        """        
        self.response = response.lower()
        self.TG_ID = TG_ID
        self.new_request = new_request


    def get_json_file(self, page: int):
        """### Данная функция предназначена для того, чтобы получать json файл, подключаясь к api сайта.

        Args:
            - response (str): Указываем наш запрос. В последствии программа переведет его в машиночитаемый формат.
            - page (int, optional): Номер страницы. По умолчанию стоит 1.
        """
        # Заголовки, передаваемые в request запросе
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
        """Парсим ранее полученный json документ.
Далее записываем его в БД. Также записываем в json файл запросы позльзователя, чтобы он смог обновить ранее сощданные БД 
        
        """        
        try:
            for page in range(1, 11):
                print(f"Парсинг страницы: {page}")
                table_name = transcription(self.response)
                data_list = self.get_json_file(page)["data"]["products"]
                for product in data_list:
                    product_url = f"https://www.wildberries.ru/catalog/{product['id']}/detail.aspx"
                    produce_name = product["name"].replace("'", "")
                    brand = product["brand"].replace("'", "")

                    try:
                        price = self.get_price(product["salePriceU"])
                    except:
                        print(f"По ссылке {product_url} \nне нашел цены")
                        price = 0
                    product_id = product["id"]
                    
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
                                url_link VARCHAR(50),
                                date_time DATETIME
                                )                    
                                """)

                    already_used = cur.execute(f"""--sql
                                                SELECT url_link FROM {table_name}
                                                """)

                    try:
                        if product_url not in str(already_used.fetchall()):
                            cur.execute(f"""--sql
                                        INSERT INTO {table_name}(
                                        product_id,
                                        product_name, 
                                        brand,
                                        current_price, 
                                        url_link,
                                        date_time)
                                        VALUES(
                                        '{product_id}',
                                        '{produce_name}', 
                                        '{brand.replace("'", "")}',
                                        {price}, 
                                        '{product_url}',
                                        '{datetime.now()}'
                                        )
                                        """)
                        else:
                            cur.execute(f"""--sql
                                        UPDATE {table_name}
                                        SET
                                        pevious_price=current_price,
                                        current_price={price},
                                        date_time='{datetime.now()}'
                                        WHERE url_link='{product_url}'
                                        """)
                        con.commit()
                    except:
                        print(produce_name, brand)

            if self.new_request is True:
                if not os.path.exists("request_data"):
                    os.mkdir("request_data")

                if not os.path.isfile(f"request_data/User_{self.TG_ID}.json"):
                    with open(f"request_data/User_{self.TG_ID}.json", "w", encoding="utf=8") as json_file:
                        json.dump(
                            {"1": [f"{self.response}", f"{table_name}"]},
                            json_file,
                            ensure_ascii=False,
                            indent=4
                        )
                else:
                    with open(f"request_data/User_{self.TG_ID}.json", "r", encoding="utf=8") as json_file:
                        data_from_json = json.load(json_file)
                        next_dict = str(len(data_from_json) + 1)
                        data_from_json[next_dict] = [f"{self.response}", f"{table_name}"]
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


    @staticmethod
    def get_price(price: str):
        '''Метод для перевода цены в удобочитаемый формат

        Args:
            price (str): Цена в строковом формате

        Returns:
            price : готовый формат цены
        '''        
        str_price = str(price)
        return "".join(list(str_price)[:-2])


def show_requests(id=0):
    '''### Показывает, какие таблицы есть в пользовательской базк данных

    Args:
        - id (int, optional): ID Пользователя телеграмма

    Returns:
        - dict: словарь с запросом и названием таблицы
    '''    
    try:
        with open(f"request_data/User_{id}.json", "r", encoding="utf-8") as json_data:
            requests_dict = json.load(json_data)
            print('\nВыберите, какой запрос исследовать: ')
            for k, v in requests_dict.items():
                print(f"{k}. {v[0]}")
            return requests_dict

    except Exception as error:
        print(error)
        quit()


def main_cycle(id=0):
    '''### Главный цикл консольного варианта программы

    Args:
        - id (int, optional): ID пользователя Telegram. Defaults to 0.
    '''

    while True:
        chose = input('''\nВыбери тип действия
new - новый запрос.
rf - обновить старый
sw - показать таблицу
q - выход 
\nЗапрос: ''')

# Создаем меню выбора действий
        match chose:
            # Новый поисковый запрос
            case "new":
                response = input('\nПоисковый запрос: ')
                wb = WBParser(response=response, TG_ID=0, new_request=True)
                wb.parse_ready_json()

            # Обновить БД
            case "rf":
                
                dict_of_requests = show_requests(id)
                chose_requsets = input("\nВыберите запись: ")
            
                refr_wb = WBParser(response=dict_of_requests[chose_requsets][0], TG_ID=0, new_request=False)
                refr_wb.parse_ready_json()

            # Просмотр БД
            case "sw":
                dict_of_requests = show_requests(id)
                chose_requsets = input("\nВыберите запись: ")

                try:
                    # Подключение к БД, создание курсора это БД
                    con = sqlite3.connect(f"databases/User_{id}.db")
                    cur = con.cursor()

                    # Вывод 20 записей, разница цен в которых больше заданного числа
                    show_db = cur.execute(f"""--sql
                                        SELECT * FROM {dict_of_requests[chose_requsets][1]} 
                                        WHERE (1-current_price/pevious_price)*100 <> 0
                                        ORDER BY current_price
                                        LIMIT 20; """)
                    for string in show_db.fetchall():
                        print(string)

                except Exception as error:
                    print(error)

            # Выход из приложения
            case "q":
                break


os.system("cls")
main_cycle()