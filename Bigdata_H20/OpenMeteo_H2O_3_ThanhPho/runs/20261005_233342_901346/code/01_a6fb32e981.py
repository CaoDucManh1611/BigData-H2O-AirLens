import subprocess, io, zipfile, shutil
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'h2o==3.46.0.8'])
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import h2o
from h2o.automl import H2OAutoML, get_leaderboard
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
plt.rcParams.update({'figure.figsize': (12, 4), 'axes.grid': True, 'grid.alpha': 0.2})

CITY_MAP = {0: 'Ha Noi', 1: 'Da Nang', 2: 'TP.HCM'}
HISTORY_NAME = 'air_quality_3_cities_20230101_20261004.csv'
FORECAST_NAME = 'forecast_3_cities_20261005_20261009.csv'
raw_dir = PROJECT / 'raw'
raw_dir.mkdir(exist_ok=True)
manifest = []
def read_source_csv(payload):
    metadata = pd.read_csv(io.BytesIO(payload), nrows=3)
    table = pd.read_csv(io.BytesIO(payload), skiprows=5)
    assert set(metadata.location_id) == {0, 1, 2}
    assert (metadata.utc_offset_seconds == 25200).all(), 'Nguồn không dùng giờ Việt Nam.'
    assert set(table.location_id) == {0, 1, 2}
    return metadata, table

with zipfile.ZipFile(SOURCE_DIR / 'Data_OpenMeteo.zip') as z:
    for filename in [HISTORY_NAME, FORECAST_NAME]:
        members = [n for n in z.namelist() if Path(n).name == filename]
        assert len(members) == 1, f'Cần đúng một file {filename}, tìm được {members}'
        payload = z.read(members[0])
        digest = hashlib.sha256(payload).hexdigest()
        target = raw_dir / filename
        if target.exists():
            assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, 'CSV raw đã khác ZIP; dừng để kiểm tra.'
        else:
            target.write_bytes(payload)  # Sao chép nguyên byte; không ghi lại bằng pandas.
        manifest.append({'file': filename, 'sha256': digest, 'bytes': len(payload)})
history_meta, raw_history = read_source_csv((raw_dir / HISTORY_NAME).read_bytes())
forecast_meta, raw_forecast = read_source_csv((raw_dir / FORECAST_NAME).read_bytes())
save_json(manifest, RUN / 'reports' / 'raw_manifest.json')
save_json({'pandas': pd.__version__, 'numpy': np.__version__, 'h2o': h2o.__version__}, RUN / 'reports' / 'versions.json')
print('Lịch sử:', raw_history.shape, '| Dự báo riêng:', raw_forecast.shape)
display(history_meta, raw_history.head(), raw_forecast.head())