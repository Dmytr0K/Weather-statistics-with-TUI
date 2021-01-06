import requests
from sqlalchemy import create_engine, Table, Column, String, Float, MetaData
from sqlalchemy.sql import select
import matplotlib.pyplot as plt
import pandas as pd
import npyscreen
import sys

class WeatherProvider:
    def __init__(self, key):
        self.key = key

    def get_data(self, location, start_date, end_date):
        url = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/history'
        params = {
            'aggregateHours': 24,
            'startDateTime': f'{start_date}T00:0:00',
            'endDateTime': f'{end_date}T23:59:59',
            'unitGroup': 'metric',
            'location': location,
            'key': self.key,
            'contentType': 'json',
        }
        data = requests.get(url, params).json()
        if data.get("errorCode","None") == "None":
            return [
                {
                    'date': row['datetimeStr'][:10],
                    'mint': row['mint'],
                    'maxt': row['maxt'],
                    'location': 'Volgograd,Russia',
                    'humidity': row['humidity'],
                }
                for row in data['locations'][location]['values']
            ]
        else:
            raise SystemError(f"Error {data['errorCode']}: {data['message']}")

class ExitButton(npyscreen.ButtonPress):
    def whenPressed(self):
        sys.exit(0)

class MainForm(npyscreen.Form):
    def create(self):
        self.nextrely += 1
        self.bd = self.add(npyscreen.TitleDateCombo, name="Begin date:")
        self.ed = self.add(npyscreen.TitleDateCombo, name="End date:")
        self.nextrely += 1
        self.exitButton = self.add(ExitButton, name="Exit")

def weather_wrapper (*args):
    Form = MainForm(name = "Volgograd weather", lines=10, columns=40)
    Form.edit()
    return {'begin': str(Form.bd.value),
            'end': str(Form.ed.value)}

if  __name__ == "__main__":
    dates = npyscreen.wrapper_basic(weather_wrapper)
    engine = create_engine('sqlite:///weather.sqlite3')
    metadata = MetaData()
    weather = Table(
        'weather',
        metadata,
        Column('date', String),
        Column('mint', Float),
        Column('maxt', Float),
        Column('location', String),
        Column('humidity', Float),
    )
    metadata.create_all(engine)

    c = engine.connect()

    provider = WeatherProvider('6BNJDB27L3LJ98UPAAMSR7GK4')

    try:
        c.execute(weather.insert(), provider.get_data('Volgograd,Russia', dates['begin'], dates['end']))

        x_dates = [row["date"] for row in c.execute(select([weather]))]
        x_dates = pd.to_datetime(x_dates)
        y_mint = [row["mint"] for row in c.execute(select([weather]))]
        y_maxt = [row["maxt"] for row in c.execute(select([weather]))]
        y_humidity = [row["humidity"] for row in c.execute(select([weather]))]
        
        #plt.xkcd()
        plt.subplot(121)
        plt.title("Min and max temperature")
        plt.xlabel("Date")
        plt.ylabel("Temperature, C")
        plt.plot(x_dates, y_mint, "b")
        plt.plot(x_dates, y_maxt, "r")
        plt.xticks(rotation=90)
        plt.subplot(122)
        plt.title("Humidity")
        plt.xlabel("Date")
        plt.ylabel("Humidity, %")
        plt.plot(x_dates, y_humidity, "--g")
        plt.xticks(rotation=90)
        plt.gcf().canvas.set_window_title("Weather")
        plt.show()

        weather.drop(engine)


    except SystemError as err:
            print(err)
