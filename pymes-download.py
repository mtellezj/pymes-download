# -*- coding: utf-8 -*-
"""Download data from the site http://pymes.org.mx
"""

import csv
import logging

import click
import requests
import tqdm
from bs4 import BeautifulSoup

LOG_FILE = 'download.log'
BASE_URL = 'https://pymes.org.mx'
URL = '{0}/municipio/{1}.html?Pyme_page={2}&municipio%2F{1}_html='

logging.basicConfig(filename=LOG_FILE, filemode='w')


def delete_last_comma(text):
    """If the last character is a comma, then delete it.

    Args:
        text (str): the text to search for a comma.

    Returns:
        str
    """
    return text[:-1] + text[-1].replace(',', '')


def get_pyme_data(url):
    """Download a pyme's page and parse it for data.

    This function search for pyme's name, street, street number,
    block, city, state, country and postal code. Some pymes do
    not has street number, so the data must be search at different
    indexes.

    Args:
        url (str): the pyme's url.

    Returns:
        list
    """
    data = scrap_page(url)
    name = data.find('span', {'itemprop': 'name'}).text

    try:
        text = data.find_all('div',
                             {'class': 'icon-box-body'})[1].stripped_strings
    except IndexError:
        raise AttributeError(f'La PYME {name} no tiene información.')
    text = [item for item in text]
    offset = 15 - len(text)

    if len(text) == 15:
        street = delete_last_comma(text[0].strip())
        number = delete_last_comma(text[1].strip())
        block = delete_last_comma(text[2].strip())
        city = delete_last_comma(text[3].strip())
        state = delete_last_comma(text[6].strip())
        country = delete_last_comma(text[8].strip())
        cp = delete_last_comma(text[10].strip())
    else:
        street = delete_last_comma(text[0].strip())
        number = ''
        block = delete_last_comma(text[1].strip())
        city = delete_last_comma(text[2].strip())
        state = delete_last_comma(text[5].strip())
        country = delete_last_comma(text[7].strip())
        cp = delete_last_comma(text[9].strip())

    return [name, street, number, block, city, state, country, cp]


def scrap_page(url):
    data = requests.get(url)

    return BeautifulSoup(data.text, 'html.parser')


def get_pymes(home):
    anchors = home.tbody.find_all('a')
    urls = [f'{BASE_URL}{url["href"]}' for url in anchors]

    return urls


@click.command()
@click.argument('municipio')
@click.option('--start', default=1, help='El número de la paginación inicial.')
@click.option('--end', default=1, help='Le número final de la paginación.')
def download(municipio, start, end):
    """Este script descarga los nombres y direcciones de las empresas
    registradas en https://pymes.org.mx.

    Para la descarga se necesita especificar el nombre del municipio como lo
    usa la página (por ejemplo Xalapa es xalapa-65eb), y el número de página de
    inicio y fin del municipio (para el caso de Xalapa existen 262 páginas).
    Para determinar el nombre del municipio hay que entrar a la liga
    https://pymes.org.mx/site/municipios.html y seleccionar el municipio
    deseado. En esa página en la barra de direcciones aparecerá el nombre del
    municipio seguido de .html. En esta página en la parte inferior aparecen
    los números de la paginación que se pueden usar como valores de inicio y fin.
    """
    assert start <= end
    with open('empresas.csv', 'w') as fp:
        writer = csv.writer(fp, delimiter=',', quotechar='"')
        writer.writerow([
            'Razón social', 'Calle', 'Número', 'Colonia', 'Ciudad', 'Estado',
            'País', 'CP'
        ])
        for page in tqdm.tqdm(range(start, end + 1), desc='Página'):
            index = scrap_page(URL.format(BASE_URL, municipio, page))
            pymes_url = get_pymes(index)
            for index in tqdm.trange(len(pymes_url), desc='PYME'):
                try:
                    info = get_pyme_data(pymes_url[index])
                    writer.writerow(info)
                except AttributeError as e:
                    logging.warning(str(e))
                except IndexError:
                    logging.error(pymes_url, exc_info=True)


if __name__ == '__main__':
    download()
