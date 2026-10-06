from google.colab import drive
drive.mount('/content/drive')
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib, json, platform, sys

SOURCE_DIR = Path('/content/drive/MyDrive/Bigdata_H20')
assert (SOURCE_DIR / 'Data_OpenMeteo.zip').is_file(), f'Không thấy ZIP trong {SOURCE_DIR}. Kiểm tra đường dẫn.'
PROJECT = SOURCE_DIR / 'OpenMeteo_H2O_3_ThanhPho'
PROJECT.mkdir(exist_ok=True)
RUN_ID = datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).strftime('%Y%m%d_%H%M%S_%f')
RUN = PROJECT / 'runs' / RUN_ID
for name in ['code', 'logs', 'reports', 'figures', 'processed', 'features', 'splits', 'metrics', 'models', 'predictions', 'notebooks']:
    (RUN / name).mkdir(parents=True, exist_ok=True)
def save_json(obj, path):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

ip = get_ipython()
# Gỡ hook của lần chạy trước để một ô chỉ ghi vào đúng lần chạy hiện tại.
for event, func in globals().get('_audit_hooks', []):
    ip.events.unregister(event, func)
_audit_counter = 0
_audit_current = None
def _audit_before(info):
    global _audit_counter, _audit_current
    _audit_counter += 1
    source = info.raw_cell
    digest = hashlib.sha256(source.encode()).hexdigest()
    path = RUN / 'code' / f'{_audit_counter:02d}_{digest[:10]}.py'
    path.write_text(source, encoding='utf-8')
    _audit_current = {'cell': _audit_counter, 'file': str(path), 'sha256': digest, 'started': datetime.now().isoformat()}
def _audit_after(result):
    if _audit_current is None:
        return
    entry = dict(_audit_current)
    entry['finished'] = datetime.now().isoformat()
    error = result.error_before_exec or result.error_in_exec
    entry['status'] = 'error' if error else 'ok'
    entry['error'] = str(error) if error else None
    with (RUN / 'logs' / 'cells.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

_audit_hooks = [('pre_run_cell', _audit_before), ('post_run_cell', _audit_after)]
for event, func in _audit_hooks:
    ip.events.register(event, func)
# Lưu cả ô thiết lập đang chạy sau khi đã kết nối Drive.
setup_source = ip.history_manager.input_hist_raw[-1]
(RUN / 'code' / '00_setup.py').write_text(setup_source, encoding='utf-8')
save_json({'run_id': RUN_ID, 'source_dir': str(SOURCE_DIR), 'target': 'next_day_mean_us_aqi',
           'source': 'CAMS model output via Open-Meteo', 'timezone': 'Asia/Ho_Chi_Minh',
           'python': sys.version, 'created': datetime.now().isoformat()}, RUN / 'reports' / 'config.json')
print('Lưu mọi đầu ra tại:', RUN)