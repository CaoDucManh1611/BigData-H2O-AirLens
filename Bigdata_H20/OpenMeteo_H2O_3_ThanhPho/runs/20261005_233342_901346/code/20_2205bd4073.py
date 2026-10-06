for item in manifest:
    assert hashlib.sha256((raw_dir / item['file']).read_bytes()).hexdigest() == item['sha256'], 'Raw CSV bị thay đổi!'
required_files = ['reports/raw_manifest.json', 'reports/split_ranges.csv', 'reports/algorithm_coverage.csv',
                  'processed/hourly_clean.csv', 'processed/daily_clean.csv', 'features/schema.json',
                  'metrics/leaderboard_validation.csv', 'metrics/family_comparison_test.csv',
                  'predictions/test_predictions.csv', 'models/leader_manifest.json']
assert all((RUN / p).is_file() for p in required_files)
# Snapshot contains exactly 13 current workflow cells, not execution-history attempts.
code_files = sorted((RUN / 'code').glob('*.py'))
workflow_files = []
for step in range(13):
    candidates = [p for p in code_files if p.name.startswith(f'{step:02d}_')]
    assert candidates, f'Missing step {step}'
    workflow_files.append(candidates[0])
for step, marker, prefix in [(2, 'raw_corr_columns =', 'def save_figure'), (4, 'quality_comparison =', 'def to_daily')]:
    candidates = [p for p in code_files if p.read_text(encoding='utf-8').startswith(prefix) and marker in p.read_text(encoding='utf-8')]
    assert candidates, f'Missing updated EDA step {step}'
    workflow_files[step] = max(candidates, key=lambda p: p.stat().st_mtime)
workflow_files[12] = Path(_audit_current['file'])
snapshot_cells = [{'cell_type':'markdown', 'metadata':{}, 'source':['# Open-Meteo H2O: current 13-step code snapshot\n', 'Run cells in order. Raw CSV is read-only. Code folder retains execution history; use this notebook for the current workflow.']}]
for step, file in enumerate(workflow_files):
    source = file.read_text(encoding='utf-8')
    compile(source, str(file), 'exec')
    snapshot_cells.append({'cell_type':'code', 'metadata':{'workflow_step':step}, 'source':source.splitlines(True), 'execution_count':None, 'outputs':[]})
assert len(snapshot_cells) == 14
save_json({'nbformat':4, 'nbformat_minor':5, 'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3'}}, 'cells':snapshot_cells}, RUN / 'notebooks' / 'OpenMeteo_H2O_code_snapshot.ipynb')
save_json([{'step':i, 'source_file':str(p.relative_to(RUN)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for i,p in enumerate(workflow_files)], RUN / 'reports' / 'current_code_manifest.json')

summary = f"""# Open-Meteo H2O — 3 thành phố
Run: {RUN_ID}
Nguồn: CAMS qua Open-Meteo; dữ liệu mô hình, không phải số đo trạm.
Mục tiêu: AQI trung bình ngày kế tiếp; horizon 1 ngày.
Lịch sử: 01/01/2023 đến 04/10/2026. Forecast lưu riêng, không train/test.
Leader chọn trên validation: {leader.model_id}
Test MAE: {leader_metrics['mae']:.4f}; RMSE: {leader_metrics['rmse']:.4f}; R2: {leader_metrics['r2']:.4f}
Các nhóm thực sự đã train: {', '.join(coverage.family)}
So sánh baseline: metrics/baseline.csv. So sánh nhóm: metrics/family_comparison_test.csv.
Raw hash đã kiểm tra lại: nội dung CSV gốc không thay đổi.
Kết quả đo khả năng dự đoán chuỗi CAMS; không chứng minh độ chính xác so với không khí đo thực tế.
Đặc trưng cần ngày đầu vào hoàn tất. Muốn dự đoán 06/10 từ dữ liệu 05/10 phải cập nhật nguồn và xác định giờ chốt.
DeepLearning và giới hạn thời gian từng model có thể làm kết quả thay đổi nhẹ giữa các lần chạy.
"""
(RUN / 'reports' / 'SUMMARY.md').write_text(summary, encoding='utf-8')
save_json({'run_id':RUN_ID, 'path':str(RUN)}, PROJECT / 'LATEST_RUN.json')
eda_required = ['figures/02_before_correlation.png', 'figures/04_before_after_aqi_histogram.png', 'figures/04_before_after_monthly_aqi.png', 'reports/before_correlation.csv', 'reports/after_correlation.csv', 'reports/before_numeric_describe.csv', 'reports/after_numeric_describe.csv', 'reports/quality_before_after.csv']
assert all((RUN / p).is_file() and (RUN / p).stat().st_size > 0 for p in eda_required)
(RUN / 'reports' / 'SUMMARY.md').write_text(summary + '\nEDA update: paired before/after histograms, monthly trend, correlation, full numeric statistics and quality checks. Snapshot has exactly 13 current workflow cells.\n', encoding='utf-8')
audit = {'checked_at':datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(), 'run_id':RUN_ID, 'raw_hash_verified':True, 'snapshot_code_cells':13, 'eda_required':eda_required, 'folders':{}}
for directory in sorted(p for p in RUN.iterdir() if p.is_dir()):
    audit['folders'][directory.name] = [{'file':str(p.relative_to(RUN)), 'bytes':p.stat().st_size} for p in sorted(directory.rglob('*')) if p.is_file()]
save_json(audit, RUN / 'reports' / 'latest_verification.json')
files = pd.DataFrame([{'file':str(p.relative_to(RUN)), 'bytes':p.stat().st_size} for p in RUN.rglob('*') if p.is_file()])
files.to_csv(RUN / 'reports' / 'file_inventory.csv', index=False)
display(files.groupby(files.file.str.split('/').str[0]).agg(files=('file','count'), bytes=('bytes','sum')))
print('HOÀN TẤT. Code, biểu đồ, splits, metrics, models đều đã lưu Drive:', RUN)
print('VERIFIED: RAW HASH OK; CURRENT SNAPSHOT = 13 CELLS; ALL 8 EDA ADDITIONS PRESENT.')
