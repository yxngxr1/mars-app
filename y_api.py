import requests
import math


def get_area_object(object):
    lower = object["boundedBy"]["Envelope"]["lowerCorner"].split(" ")
    upper = object["boundedBy"]["Envelope"]["upperCorner"].split(" ")
    upper, lower = list(map(float, upper)), list(map(float, lower))
    delta1 = str((upper[0] - lower[0]) / 3)
    delta2 = str((upper[1] - lower[1]) / 3)
    return delta1, delta2


def get_toponym_by_address(address):
    api_server = "http://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": address,
        "format": "json"}

    response = requests.get(api_server, params=params)

    if not response:
        print(f'Ошибка: {response.status_code}')
        exit(1)
        pass

    json_response = response.json()
    toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
    return toponym


def lonlat_distance(a, b):
    degree_to_meters_factor = 111 * 1000  # 111 километров в метрах
    a_lon, a_lat = a
    b_lon, b_lat = b

    # Берем среднюю по широте точку и считаем коэффициент для нее.
    radians_lattitude = math.radians((a_lat + b_lat) / 2.)
    lat_lon_factor = math.cos(radians_lattitude)

    # Вычисляем смещения в метрах по вертикали и горизонтали.
    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor

    # Вычисляем расстояние между точками.
    distance = math.sqrt(dx * dx + dy * dy)

    return distance
