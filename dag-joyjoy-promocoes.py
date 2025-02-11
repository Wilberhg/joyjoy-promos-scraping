import logging
from logging import StreamHandler

log_format = log_format = "%(asctime)s - %(levelname)s: %(message)s"
logging.basicConfig(
    format=log_format,
    level=logging.INFO,
    datefmt="%H:%M:%S",
    handlers=[StreamHandler()],
)

import httpx
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from random import randint
import time
from datetime import datetime

ua = UserAgent(platforms="desktop")

with httpx.Client(base_url="https://joyjoy.dooca.store", headers={"user-agent": ua.random}) as client:
    params = {"page": 1}
    board_games_list = []
    while True:
        response = client.get(
            "/jogos-de-tabuleiro",
            params={"promotion": 1, "limit": 48, "grid": 4, **params},
        )
        logging.info(
            f'Realizado requisição no endpoint "{response.url}" e o status foi "{response.status_code}"'
        )
        soup = BeautifulSoup(response.content, "html.parser")
        board_game_area = soup.find("div", class_="col order-1")
        board_game_items = board_game_area.find_all("div", class_="product-card")
        if board_game_items:
            logging.info(
                f"Localizado {len(board_game_items)} jogos de tabuleiro em promoção"
            )
            for board_game in board_game_items:
                page_board_game_link = board_game.attrs["data-product-url"]
                name = board_game.attrs["data-product-name"]
                variation_id = board_game.attrs["data-product-variation-id"]
                pix_price_element = board_game.find("div", class_="pix")
                if pix_price_element:
                    pix_price_value = pix_price_element.find("span", class_="price total").text
                    pix_price_value += " no pix"
                    credit_card_price_element = board_game.find("div", class_="installments")
                    credit_card_price_value = " ".join(
                        [
                            price_value.text.strip()
                            for price_value in credit_card_price_element.find_all("span")
                        ]
                    )
                    board_game_details = {
                        "id": variation_id,
                        "name": name,
                        "pixPrice": pix_price_value,
                        "creditCardPrice": credit_card_price_value,
                        "boardGamePage": page_board_game_link,
                        "dataExtracao": datetime.today().timestamp(),
                    }
                    logging.info(f'Realizado coleta do jogo "{board_game_details}"')
                    board_games_list.append(board_game_details)
                else:
                    logging.info("Chegado à categoria de jogos vendidos")
                    break
            params["page"] += 1
            time.sleep(randint(1, 5))
        else:
            logging.info("Chegado a página pós-final dos jogos de tabuleiro")
            break
        logging.info(f'Parâmetro página incrementado 1 - "{params["page"]}"')
    print(board_games_list)

from tinydb import TinyDB, Query

Joyjoy = Query()
with TinyDB("board_games.json") as db:
    db.default_table_name = "Joyjoy"
    for board_game in board_games_list:
        board_game = {**board_game, "reportado": 0}
        db.upsert(board_game, ((Joyjoy.id == board_game["id"]) & (Joyjoy.pixPrice == board_game["pixPrice"]) & (Joyjoy.creditCardPrice == board_game["creditCardPrice"])))

# from tinydb import TinyDB

# db = TinyDB("board_games.json")
# db.default_table_name = "Joyjoy"
# db.insert_multiple(board_games_list)

from tinydb import Query

with TinyDB("board_games.json") as db:
    db.default_table_name = "Joyjoy"
    Joyjoy = Query()
    jogos_nao_reportados = db.search(Joyjoy.reportado == 0)
    ...