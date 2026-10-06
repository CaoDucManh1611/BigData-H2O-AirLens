"""Local H2O MOJO scoring demo. Original project files are read-only."""
import csv
import io
import json
import math
import os
import re
import statistics
import subprocess
import tempfile
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen, Request

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('AIR_DATA_ROOT', str(HERE.parent)))
PROJECT = ROOT / 'OpenMeteo_H2O_3_ThanhPho'
if not PROJECT.exists():
    PROJECT = Path('C:/DoAn_H20_2/OpenMeteo_H2O_3_ThanhPho')
RUN_ID = json.loads((PROJECT / 'LATEST_RUN.json').read_text(encoding='utf-8-sig'))['run_id']
if not re.fullmatch(r'\d{8}_\d{6}_\d{6}', RUN_ID):
    raise ValueError('Invalid run ID')
RUN = PROJECT / 'runs' / RUN_ID
MANIFEST = json.loads((RUN / 'models/leader_manifest.json').read_text(encoding='utf-8-sig'))
SCHEMA = json.loads((RUN / 'features/schema.json').read_text(encoding='utf-8-sig'))
assert MANIFEST['predictors'] == SCHEMA['predictors']
MOJO = RUN / 'models' / (MANIFEST['leader'] + '.zip')
JAR = RUN / 'models/h2o-genmodel.jar'
JAVA = next((HERE / 'runtime').glob('*/bin/java.exe'), None)
if JAVA is None:
    raise RuntimeError('Missing portable Java in Demo/runtime')
assert MOJO.is_file() and JAR.is_file()
VN = timezone(timedelta(hours=7))
CITIES = {'Ha Noi': {'label': 'Hà Nội', 'lat': 21.0285, 'lon': 105.8542},
          'Da Nang': {'label': 'Đà Nẵng', 'lat': 16.0544, 'lon': 108.2022},
          'TP.HCM': {'label': 'TP. Hồ Chí Minh', 'lat': 10.8231, 'lon': 106.6297}}
VALUES = ['pm10', 'pm2_5', 'co', 'no2', 'so2', 'o3', 'aqi']

def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def load_daily():
    result = {city: {} for city in CITIES}
    for row in read_csv(RUN / 'processed/daily_clean.csv'):
        city = row['city']
        if city not in result:
            raise ValueError('Unknown city in dataset')
        if float(row['hour_count']) != 24 or float(row['aqi_count']) != 24:
            continue
        values = {key: float(row[key]) for key in VALUES + ['aqi_max', 'pm2_5_std']}
        if not all(math.isfinite(v) and v >= 0 for v in values.values()):
            raise ValueError('Invalid daily values')
        result[city][date.fromisoformat(row['date'][:10])] = values
    return result

DAILY = load_daily()
EVALUATION = json.loads((RUN / 'metrics/leader_test.json').read_text(encoding='utf-8-sig'))
COMPARISON = read_csv(RUN / 'metrics/family_comparison_test.csv')

def features(city, day, daily):
    """Same 21 predictors, lag definition and calendar as notebook step 5."""
    if city not in CITIES:
        raise ValueError('Thành phố không hợp lệ.')
    history = []
    for lag in range(8):
        item = daily[city].get(day - timedelta(days=lag))
        if item is None:
            raise ValueError('Cần đủ 8 ngày liên tiếp, mỗi ngày đủ 24 giá trị theo giờ.')
        history.append(item)
    target = day + timedelta(days=1)
    result = {'city': city}
    result.update({key + '_today': history[0][key] for key in VALUES + ['aqi_max', 'pm2_5_std']})
    result.update({f'aqi_lag_{lag}': history[lag]['aqi'] for lag in [1, 2, 3, 7]})
    for window in [3, 7]:
        for key in ['aqi', 'pm2_5']:
            result[f'{key}_mean_{window}'] = statistics.mean(row[key] for row in history[:window])
    doy = target.timetuple().tm_yday
    result.update(weekday=target.weekday(), year_sin=math.sin(2*math.pi*doy/365.25), year_cos=math.cos(2*math.pi*doy/365.25))
    assert set(result) == set(SCHEMA['predictors'])
    return result

def score(rows):
    # ponytail: one JVM per scoring batch; a persistent Java service if traffic grows.
    with tempfile.TemporaryDirectory(prefix='airlens_') as temp:
        inp, out = Path(temp) / 'input.csv', Path(temp) / 'output.csv'
        with inp.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=SCHEMA['predictors'])
            writer.writeheader(); writer.writerows(rows)
        cmd = [str(JAVA), '-Xmx1g', '-cp', str(JAR), 'hex.genmodel.tools.PredictCsv',
               '--mojo', str(MOJO), '--input', str(inp), '--output', str(out), '--decimal']
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if process.returncode:
            raise RuntimeError('MOJO scoring failed: ' + process.stderr[-1800:])
        predictions = [float(row['predict']) for row in read_csv(out)]
        if len(predictions) != len(rows) or not all(math.isfinite(p) for p in predictions):
            raise RuntimeError('Model trả về kết quả không hợp lệ.')
        return predictions

def fetch_current():
    today = datetime.now(VN).date()
    query = urlencode({'latitude': ','.join(str(c['lat']) for c in CITIES.values()),
                       'longitude': ','.join(str(c['lon']) for c in CITIES.values()),
                       'hourly': 'pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi',
                       'timezone': 'Asia/Ho_Chi_Minh', 'start_date': str(today-timedelta(days=13)), 'end_date': str(today)})
    url = 'https://air-quality-api.open-meteo.com/v1/air-quality?' + query
    with urlopen(Request(url, headers={'User-Agent': 'AirLens-Academic-Demo/1.0'}), timeout=35) as response:
        body = response.read(8_000_001)
    if len(body) > 8_000_000:
        raise ValueError('API response too large')
    payload = json.loads(body)
    if not isinstance(payload, list) or len(payload) != 3:
        raise ValueError('API không trả đủ ba thành phố.')
    result = {city: {} for city in CITIES}
    mapping = dict(zip(VALUES, ['pm10','pm2_5','carbon_monoxide','nitrogen_dioxide','sulphur_dioxide','ozone','us_aqi']))
    for city, location in zip(CITIES, payload):
        if location.get('utc_offset_seconds') != 25200:
            raise ValueError('API timezone mismatch')
        expected = CITIES[city]
        if abs(location['latitude'] - expected['lat']) > 0.6 or abs(location['longitude'] - expected['lon']) > 0.6:
            raise ValueError('API city grid mismatch')
        hourly = location['hourly']; grouped = {}
        for i, timestamp in enumerate(hourly['time']):
            point = datetime.fromisoformat(timestamp)
            values = {}
            for key, api_key in mapping.items():
                value = hourly[api_key][i]
                if value is None or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    raise ValueError('API có dữ liệu thiếu/không hợp lệ; không tự điền số.')
                values[key] = value
            grouped.setdefault(point.date(), []).append((point.hour, values))
        for day, rows in grouped.items():
            if len(rows) != 24 or {hour for hour, _ in rows} != set(range(24)):
                continue
            values = {key: statistics.mean(row[key] for _, row in rows) for key in VALUES}
            values.update(aqi_max=max(row['aqi'] for _, row in rows), pm2_5_std=statistics.stdev(row['pm2_5'] for _, row in rows))
            result[city][day] = values
        features(city, today, result)  # Require complete continuous input history.
    return result, today, url

def make_prediction(city, day, daily, mode, api_url=None):
    row = features(city, day, daily)
    prediction = score([row])[0]
    history = [{'date': str(day-timedelta(days=lag)), 'aqi': daily[city][day-timedelta(days=lag)]['aqi']}
               for lag in range(13, -1, -1) if day-timedelta(days=lag) in daily[city]]
    result = {'city': city, 'label': CITIES[city]['label'], 'input_date': str(day), 'target_date': str(day+timedelta(days=1)),
              'prediction': prediction, 'today_aqi': row['aqi_today'], 'history': history,
              'mode': mode, 'features': row, 'model_id': MANIFEST['leader'],
              'source': 'CAMS / Open-Meteo', 'retrieved_at': datetime.now(VN).isoformat(), 'api_url': api_url}
    # Demo output is separate; never overwrite downloaded CSV/model files.
    exports = HERE / 'exports'; exports.mkdir(exist_ok=True)
    name = datetime.now(VN).strftime('%Y%m%d_%H%M%S_%f') + '.json'
    (exports / name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result

def state():
    available = sorted(set.intersection(*(set(days) for days in DAILY.values())))
    available = [day for day in available if all(day-timedelta(days=7) in days for days in DAILY.values())]
    return {'cities': [{'id': c, **info} for c, info in CITIES.items()], 'dates': [str(d) for d in available[-90:]],
            'latest_date': str(available[-1]), 'evaluation': EVALUATION, 'comparison': COMPARISON, 'model_id': MANIFEST['leader']}

class Handler(BaseHTTPRequestHandler):
    def send_json(self, body, status=200):
        data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store')
        self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/state':
            return self.send_json(state())
        figures = {p.name: p for p in (RUN / 'figures').glob('*.png')}
        if path in ['/', '/index.html', '/overview'] or path in {'/figures/' + name for name in figures}:
            file = figures[path.removeprefix('/figures/')] if path.startswith('/figures/') else HERE / ('overview.html' if path == '/overview' else 'index.html')
            data = file.read_bytes()
            self.send_response(200); self.send_header('Content-Type','image/png' if path.startswith('/figures/') else 'text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
        else:
            self.send_error(404)

    def do_POST(self):
        if urlparse(self.path).path != '/api/predict':
            return self.send_error(404)
        origin = self.headers.get('Origin')
        if origin and origin not in ['http://127.0.0.1:8766','http://localhost:8766']:
            return self.send_json({'error':'Origin không hợp lệ.'},403)
        try:
            length = int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 4096:
                raise ValueError('Request size invalid')
            body = json.loads(self.rfile.read(length))
            city = body.get('city')
            if city not in CITIES:
                raise ValueError('Thành phố không hợp lệ.')
            mode = body.get('mode')
            if mode == 'live':
                daily, day, url = fetch_current()
                prediction = make_prediction(city, day, daily, mode, url)
            elif mode == 'snapshot':
                day = date.fromisoformat(body['date'])
                prediction = make_prediction(city, day, DAILY, mode)
            else:
                raise ValueError('Chế độ không hợp lệ.')
            self.send_json(prediction)
        except (ValueError, KeyError) as error:
            self.send_json({'error':str(error)},400)
        except Exception as error:
            print(type(error).__name__, str(error), flush=True)
            self.send_json({'error':'Không lấy được dữ liệu hoặc chạy model. Kiểm tra kết nối mạng, hoặc dùng dữ liệu đã tải. Chi tiết: '+str(error)[:250]},503)

def check():
    samples = read_csv(RUN / 'splits/test.csv')[::50]
    rows = [features(row['city'], date.fromisoformat(row['input_date'][:10]), DAILY) for row in samples]
    for row, saved in zip(rows, samples):
        for key in SCHEMA['predictors']:
            assert row[key] == saved[key] if key == 'city' else math.isclose(row[key], float(saved[key]), rel_tol=1e-10, abs_tol=1e-10), key
    predictions = score(rows)
    reference = {(r['city'],r['input_date'][:10]):float(r['prediction']) for r in read_csv(RUN / 'predictions/test_predictions.csv')}
    errors = [abs(p-reference[(r['city'],r['input_date'][:10])]) for p,r in zip(predictions,samples)]
    assert max(errors) < 1e-5, f'MOJO does not match Colab: {max(errors)}'
    print(f'PASS: {len(samples)} rows, features match Colab; MOJO max difference {max(errors):.10f}',flush=True)

if __name__ == '__main__':
    import sys
    if '--check' in sys.argv:
        check()
    else:
        print('AirLens: http://127.0.0.1:8766',flush=True)
        ThreadingHTTPServer(('127.0.0.1',8766),Handler).serve_forever()
