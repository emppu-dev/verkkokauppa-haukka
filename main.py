import requests
from lxml import html
import configparser
import time, datetime
import json

config = configparser.ConfigParser()
config.read("config.ini")

odotus = int(config.get("asetukset", "odotus"))
discord_webhook = str(config.get("asetukset", "discord_webhook"))

def log(text):
    timestamp = datetime.datetime.utcfromtimestamp(time.time()).strftime("%H:%M:%S")
    print(f"[{timestamp}] {text}")

try:
    with open("linkit.txt", "r") as linkit_file:
        linkit = linkit_file.read().splitlines()
        log(f"{len(linkit)} linkkiä asetettu")
except FileNotFoundError:
    log("linkit.txt tiedostoa ei löytynyt")
    exit()

last_prices = {}

with requests.Session() as session:
    log("Pidetään kirjaa hintamuutoksista...")
    while True:
        for url in linkit:
            try:
                r = session.get(url)
                if r.status_code == 200:
                    tree = html.fromstring(r.text)

                    otsikko = tree.xpath("/html/body/div[1]/div[1]/div/div[2]/div[1]/main/div/div[2]/header/h1")
                    hinta = tree.xpath("/html/body/div[1]/div[1]/div/div[2]/div[1]/main/div/div[2]/aside/div[2]/div/div[1]/div/div[1]/span/data")

                    if hinta and otsikko:
                        product_name = otsikko[0].text_content()
                        current_price = hinta[0].text_content()

                        if url in last_prices and last_prices[url] != current_price:
                            log(f"Hinta muuttui!!!, {product_name}: {current_price}")
                            embed_data = {"title": "Hinta muuttui","fields": [{"name": "Tuote","value": f"```{product_name}```","inline": True},{"name": "Uusi hinta","value": f"```{current_price}```","inline": True},{"name": "Linkki","value": f"```{url}```","inline": False}]}
                            payload = {"embeds": [embed_data]}
                            response = requests.post(discord_webhook, data=json.dumps(payload), headers={"Content-Type": "application/json"})

                            if response.status_code == 200:
                                log("Hinta muutos lähettetty Discord webhookkiin")
                            else:
                                log(f"Jotain meni mönkään")

                        last_prices[url] = current_price
                    else:
                        log("Otsikkoa tai hintaa ei löytynyt sivulta. Tarkista linkki.")
                else:
                    log(f"Jotain meni mönkään")

            except Exception as e:
                log(f"Virhe sivun hakemisessa: {str(e)}")

        time.sleep(odotus)