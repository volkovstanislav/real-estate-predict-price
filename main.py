import os
import data
import folium
import pickle
import numpy as np
import pandas as pd
from flask_wtf import FlaskForm
from flask import Flask, render_template, request
from wtforms.validators import InputRequired, NumberRange
from wtforms import SubmitField, FloatField, IntegerField, SelectField, BooleanField


class ModelForm(FlaskForm):
    area = FloatField('area', validators=[InputRequired()])
    floor = IntegerField('floor', validators=[InputRequired()])
    total_floors = IntegerField('total_floors', validators=[InputRequired()])
    lat = FloatField('lat', validators=[NumberRange(min=-90, max=90), InputRequired()])
    lon = FloatField('lon', validators=[NumberRange(min=-180, max=180), InputRequired()])
    ad_type = SelectField(
        "Выберите тип объявления",
        choices=[(1, "Продажа"), (2, "Аренда")],
    )
    dist = SelectField(
        'District',
        choices=data.district
    )
    rooms = SelectField(
        'Rooms',
        choices=data.rooms
    )
    first_floor = BooleanField(
        label='Первый этаж'
    )
    last_floor = BooleanField(
        label='Последний этаж'
    )
    seria = SelectField(
        label='Серия дома',
        choices=data.house_seria
    )
    type = SelectField(
        label="Тип дома",
        choices=data.house_type
    )
    cond = SelectField(
        label="Удобства",
        choices=data.conditional
    )
    submit = SubmitField()


app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.route('/')
def hello():
    form = ModelForm(dist='district_Iļģuciems', lat=24.1, lon=56.9)
    output = render_template("main.html", form=form)
    return output


@app.route('/predict/', methods=['GET', 'POST'])
def render_predict():
    form = ModelForm()
    if request.method == 'POST':
        if form.validate():
            res = {
                'area': form.area.data,
                'ad_type': form.ad_type.data,
                'floor': form.floor.data,
                'total_floors': form.total_floors.data,
                'lat': form.lat.data,
                'lon': form.lon.data,
                'dist': form.dist.data,
                'rooms': form.rooms.data,
                'first_floor': form.first_floor.data,
                'last_floor': form.last_floor.data,
                'seria': form.seria.data,
                'type': form.type.data,
                'cond': form.cond.data
            }

            if res['ad_type'] == '1':
                # Загружаем модель
                with open("data/model_for_sale.pickle", "rb") as pickle_file:
                    model = pickle.load(pickle_file)
                # Загружаем данные по продаже для отображения на карте
                with open("data/df_sale.pickle", "rb") as pickle_file:
                    df = pickle.load(pickle_file)
            else:
                # Загружаем модель
                with open("data/model_for_rent.pickle", "rb") as pickle_file:
                    model = pickle.load(pickle_file)
                # Загружаем данные по аренде для отображения на карте
                with open("data/df_rent.pickle", "rb") as pickle_file:
                    df = pickle.load(pickle_file)

            template_answer = pd.read_csv("data/template.csv")
            template_answer.loc[0, "area"] = res["area"]
            template_answer.loc[0, "floor"] = res["floor"]
            template_answer.loc[0, "total_floors"] = res["total_floors"]
            template_answer.loc[0, "lat"] = res["lat"]
            template_answer.loc[0, "lon"] = res["lon"]
            template_answer.loc[0, res["dist"]] = 1
            template_answer.loc[0, res["rooms"]] = 1
            template_answer.loc[0, res["seria"]] = 1
            template_answer.loc[0, res["type"]] = 1
            template_answer.loc[0, res["cond"]] = 1
            template_answer.loc[0, "flag_first_floor"] = res["first_floor"]
            template_answer.loc[0, "flag_last_floor"] = res["last_floor"]

            # Предсказываем цену
            predict = int(np.exp(model.predict(template_answer)[0]))

            # Фильтруем по указанному району
            df = df[df[res["dist"]] == 1]

            # Находим похожие по цене объекты
            df = df.iloc[(df['price'] - predict).abs().values.argsort()[:10]]
            df = df[["area", "floor", "total_floors", "price", "lat", "lon"]]

            if df.shape[0] != 0:
                start_coords = (df["lat"].mean(), df["lon"].mean())
            else:
                start_coords = (24.1, 56.9)
            riga_map = folium.Map(location=start_coords, zoom_start=14)
            for k, v in df.iterrows():
                text = f"area: {v['area']}, floor:{v['area']}, price:{v['price']}"
                folium.Marker(location=(v["lat"], v["lon"]), popup=text)\
                    .add_to(riga_map)

            riga_map.save('templates/map.html')

            output = render_template("predict.html", pred=predict, res=res)
        else:
            output = render_template("predict.html")
    else:
        output = render_template("predict.html")
    return output


@app.route('/info/')
def render_info():
    output = render_template("info.html")
    return output

if __name__ == '__main__':
    app.run()
#app.run('0.0.0.0', 8000, debug=True)
