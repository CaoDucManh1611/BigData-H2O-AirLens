for item in manifest:
    assert hashlib.sha256((raw_dir / item['file']).read_bytes()).hexdigest() == item['sha256'], 'Raw CSV bị thay đổi!'
required_files = ['reports/raw_manifest.json', 'reports/split_ranges.csv', 'reports/algorithm_coverage.csv',
                  'processed/hourly_clean.csv', 'processed/daily_clean.csv', 'features/schema.json',
                  'metrics/leaderboard_validation.csv', 'metrics/family_comparison_test.csv',
                  'predictions/test_predictions.csv', 'models/leader_manifest.json']
assert all((RUN / p).is_file() for p in required_files)
code_files = sorted((RUN / 'code').glob('*.py'))
assert len(code_files) >= 13, f'Thiếu file code: chỉ có {len(code_files)}'
snapshot_cells = [{'cell_type':'markdown', 'metadata':{}, 'source':['# Open-Meteo H2O: code snapshot\n', 'Run cells in order. Raw CSV is read-only.']}]
for file in code_files:
    snapshot_cells.append({'cell_type':'code', 'metadata':{}, 'source':file.read_text(encoding='utf-8').splitlines(True), 'execution_count':None, 'outputs':[]})
save_json({'nbformat':4, 'nbformat_minor':5, 'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3'}},
           'cells':snapshot_cells}, RUN / 'notebooks' / 'OpenMeteo_H2O_code_snapshot.ipynb')
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
files = pd.DataFrame([{'file':str(p.relative_to(RUN)), 'bytes':p.stat().st_size} for p in RUN.rglob('*') if p.is_file()])
files.to_csv(RUN / 'reports' / 'file_inventory.csv', index=False)
display(files.groupby(files.file.str.split('/').str[0]).agg(files=('file','count'), bytes=('bytes','sum')))
print('HOÀN TẤT. Code, biểu đồ, splits, metrics, models đều đã lưu Drive:', RUN)