from dadata import Dadata
import numpy as np

class GeoStuff:
  __token = 'b1cb636401c67d041c63d1f1c15eefd48197e899'
  dadata = Dadata(__token)

  @staticmethod
  def get_coordinates(address):
    """
    Возвращает координаты по адресу

    :address str address: Строка-адрес
    """

    query_result = GeoStuff.dadata.suggest("address", address)
    y, x = query_result[0]['data']['geo_lat'], query_result[0]['data']['geo_lon']
    return (float(x), float(y))

  @staticmethod
  def calculate_time(location1, location2):
    """
    Считает время в пути между двумя адресами

    :param tuple location1: Координаты начальной точки
    :param tuple location2: Координаты конечной точки
    """
    
    online_events_designations = ['online', None]
    if (location1 in online_events_designations) or (location2 in online_events_designations):
      return 0
    x1, y1 = GeoStuff.get_coordinates(location1)
    x2, y2 = GeoStuff.get_coordinates(location2)
    Earth_r = 6371 # km
    dphi = abs(y1 - y1) * np.pi / 180
    phim = (y1 + y2) * np.pi / 360
    dlam = abs(x1 - x2) * np.pi / 180
    dist = Earth_r * (dphi ** 2 + (np.cos(phim) * dlam) ** 2) ** 0.5
    speed = 25 if dist > 3 else 5
    return dist / speed