from google.colab import files
import zipfile
with zipfile.ZipFile('/content/before_correlation_update.zip', 'w') as corr_zip:
    for p in [RUN / 'figures' / '02_before_correlation.png', RUN / 'reports' / 'before_correlation.csv']:
        corr_zip.write(p, p.name)
files.download('/content/before_correlation_update.zip')
