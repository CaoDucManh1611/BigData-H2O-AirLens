from google.colab import files
import zipfile
paired_files = ['figures/04_before_after_aqi_histogram.png', 'figures/04_before_after_monthly_aqi.png', 'reports/quality_before_after.csv', 'reports/after_correlation.csv', 'reports/before_numeric_describe.csv', 'reports/after_numeric_describe.csv']
with zipfile.ZipFile('/content/paired_eda_update.zip', 'w') as paired_zip:
    for name in paired_files:
        paired_zip.write(RUN / name, name)
    for marker, name in [('Pearson correlation of original hourly', 'code/02_updated.py'), ('Paired EDA: same bins', 'code/04_updated.py')]:
        candidates = [p for p in (RUN / 'code').glob('*.py') if marker in p.read_text(encoding='utf-8')]
        candidate = max(candidates, key=lambda p: p.stat().st_mtime)
        paired_zip.write(candidate, name)
files.download('/content/paired_eda_update.zip')
print('DOWNLOAD READY: paired_eda_update.zip')
