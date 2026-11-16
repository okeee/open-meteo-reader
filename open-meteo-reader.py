#!/usr/bin/env python3
"""指定した地点の天気と大気質を Open-Meteo から取得し、JSON オブジェクト 1 つとして標準出力に出す。"""
import argparse
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# (Open-Meteo の変数名, 出力するフィールド名)
WEATHER = [
    ("temperature_2m", "temperature"),            # 気温 (℃)
    ("relative_humidity_2m", "humidity"),         # 相対湿度 (%)
    ("apparent_temperature", "apparent_temperature"),  # 体感温度 (℃)
    ("weather_code", "code"),                     # 天気 (WMO コード)
    ("cloud_cover", "cloud_cover"),               # 雲量 (%)
    ("precipitation", "precipitation"),           # 降水量 (mm)
    ("shortwave_radiation", "radiation"),         # 日射量 (W/m²)
    ("wind_speed_10m", "wind_speed"),             # 風速 (km/h)
    ("surface_pressure", "pressure"),             # 気圧 (hPa)
]
AIR_QUALITY = [
    ("pm2_5", "pm2_5"),              # PM2.5 (μg/m³)
    ("pm10", "pm10"),                # PM10 (μg/m³)
    ("nitrogen_dioxide", "no2"),     # 二酸化窒素 (μg/m³)
    ("ozone", "o3"),                 # オゾン (μg/m³)
    ("carbon_monoxide", "co"),       # 一酸化炭素 (μg/m³)
    ("sulphur_dioxide", "so2"),      # 二酸化硫黄 (μg/m³)
    ("us_aqi", "us_aqi"),            # 米国 AQI
]


def fetch(url: str, lat: float, lon: float, variables: list, prefix: str, timeout: float) -> dict:
    query = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "current": ",".join(v for v, _ in variables),
        "timezone": "UTC",
    })
    req = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": "open-meteo-reader"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        current = json.load(r).get("current", {})
    return {f"{prefix}{name}": current[v] for v, name in variables if current.get(v) is not None}


def load_cache(path: str, max_age: float):
    try:
        if time.time() - os.path.getmtime(path) <= max_age:
            with open(path) as f:
                return json.load(f)
    except (OSError, ValueError):
        pass
    return None


def save_cache(path: str, record: dict):
    d = os.path.dirname(os.path.abspath(path))
    with tempfile.NamedTemporaryFile("w", dir=d, delete=False) as f:
        json.dump(record, f)
    os.replace(f.name, path)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--latitude", type=float, required=True, help="緯度")
    p.add_argument("--longitude", type=float, required=True, help="経度")
    p.add_argument("--weather-prefix", default="weather_", help="天気のフィールド名の接頭辞")
    p.add_argument("--air-prefix", default="air_", help="大気質のフィールド名の接頭辞")
    p.add_argument("--no-air-quality", action="store_true", help="大気質を取得しない")
    p.add_argument("--cache", help="結果を保存するファイル。指定すると --cache-ttl 秒以内は API を呼ばずにこれを出す")
    p.add_argument("--cache-ttl", type=float, default=600, help="キャッシュを使う秒数 (Open-Meteo の current は 15 分ごとの値)")
    p.add_argument("--max-stale", type=float, default=3600, help="API が失敗したとき、この秒数以内のキャッシュなら代わりに出す")
    p.add_argument("--timeout", type=float, default=10, help="API 1 回あたりのタイムアウト (秒)")
    args = p.parse_args()

    if args.cache and (cached := load_cache(args.cache, args.cache_ttl)) is not None:
        print(json.dumps(cached))
        return 0

    targets = [(FORECAST_URL, WEATHER, args.weather_prefix)]
    if not args.no_air_quality:
        targets.append((AIR_QUALITY_URL, AIR_QUALITY, args.air_prefix))

    record, failed = {}, False
    for url, variables, prefix in targets:
        try:
            record.update(fetch(url, args.latitude, args.longitude, variables, prefix, args.timeout))
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            print(f"open-meteo error ({url}): {e}", file=sys.stderr)
            failed = True

    if failed and args.cache and (stale := load_cache(args.cache, args.max_stale)) is not None:
        print(json.dumps({**stale, **record}))  # 取れた分は新しい値で上書きする
        return 0
    if not record:
        return 1
    if args.cache and not failed:
        save_cache(args.cache, record)
    print(json.dumps(record))
    return 0


if __name__ == "__main__":
    sys.exit(main())
