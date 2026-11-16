# open-meteo-reader

指定した地点の天気と大気質を [Open-Meteo](https://open-meteo.com/) から取得し、JSON オブジェクト 1 つとして標準出力に出すコマンドです。

[harvest-relay](https://github.com/okeee/harvest-relay) の poll センサーとして使うと、室内のセンサーの値と同じ行で SORACOM Harvest Data に送れるので、室内と屋外の値を並べて比べられます。

```console
$ open-meteo-reader --latitude 35.68 --longitude 139.77
{"weather_temperature": 17.5, "weather_humidity": 55, "weather_apparent_temperature": 15.3, "weather_code": 0, "weather_cloud_cover": 0, "weather_precipitation": 0.0, "weather_radiation": 531.0, "weather_wind_speed": 11.8, "weather_pressure": 1013.5, "air_pm2_5": 9.0, "air_pm10": 9.5, "air_no2": 17.4, "air_o3": 75.0, "air_co": 186.0, "air_so2": 15.5, "air_us_aqi": 120}
```

| フィールド | 内容 |
|---|---|
| weather_temperature | 気温 (℃) |
| weather_humidity | 相対湿度 (%) |
| weather_apparent_temperature | 体感温度 (℃) |
| weather_code | 天気 ([WMO コード](https://open-meteo.com/en/docs#weather_variable_documentation)。0 = 快晴、61 = 弱い雨など) |
| weather_cloud_cover | 雲量 (%) |
| weather_precipitation | 降水量 (mm) |
| weather_radiation | 日射量 (W/m²) |
| weather_wind_speed | 風速 (km/h) |
| weather_pressure | 地上気圧 (hPa) |
| air_pm2_5 / air_pm10 | PM2.5 / PM10 (μg/m³) |
| air_no2 / air_o3 / air_co / air_so2 | 二酸化窒素 / オゾン / 一酸化炭素 / 二酸化硫黄 (μg/m³) |
| air_us_aqi | 米国 AQI |

接頭辞は `--weather-prefix` / `--air-prefix` で変えられます。大気質が不要なら `--no-air-quality` を付けます。

## 注意点

- 値は観測値ではなく、Open-Meteo の予報モデルによる推定値です。天気は 15 分ごと、大気質は 1 時間ごとに更新されます
- 緯度・経度から住んでいる場所が分かるので、設定ファイルを公開するときは消してください。小数第 2 位 (約 1 km) まで丸めても値はほとんど変わりません
- Open-Meteo の無料 API は非商用利用に限られ、1 日 10,000 回までです。1 分ごとに実行すると 1 回の実行で 2 回呼ぶため 1 日 2,880 回になりますが、`--cache` を付けると `--cache-ttl` 秒 (既定 600 秒) は前回の値を出すので 1 日 300 回程度に減ります
- `--cache` を付けていれば、API が失敗したときも `--max-stale` 秒 (既定 3600 秒) 以内の前回の値を出します
- データは [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) で提供されています。グラフなどを公開するときは「Weather data by Open-Meteo.com」と出典を書いてください

## 必要なもの

- Python 3.11 以上 (標準ライブラリのみで動きます)
- API キーは不要です

## セットアップ

```bash
sudo install -m 755 open-meteo-reader.py /usr/local/bin/open-meteo-reader
open-meteo-reader --latitude 35.68 --longitude 139.77
```

### harvest-relay で Harvest Data に送る

[harvest-relay.example.toml](harvest-relay.example.toml) の `[[source]]` を harvest-relay の設定ファイルに加え、緯度・経度を自分の地点に置き換えます。

## ライセンス

MIT
