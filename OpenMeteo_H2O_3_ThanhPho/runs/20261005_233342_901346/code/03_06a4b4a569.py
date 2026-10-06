RENAME = {'pm10 (μg/m³)': 'pm10', 'pm2_5 (μg/m³)': 'pm2_5',
          'carbon_monoxide (μg/m³)': 'co', 'nitrogen_dioxide (μg/m³)': 'no2',
          'sulphur_dioxide (μg/m³)': 'so2', 'ozone (μg/m³)': 'o3', 'us_aqi (USAQI)': 'aqi'}
VALUES = list(RENAME.values())
def clean_hourly(raw):
    data = raw.rename(columns=RENAME).copy()
    assert all(c in data.columns for c in VALUES)
    data['time'] = pd.to_datetime(data['time'], errors='raise')
    data['city'] = data.location_id.map(CITY_MAP)
    assert data.city.notna().all()
    for col in VALUES:
        data[col] = pd.to_numeric(data[col], errors='coerce')
        data.loc[~np.isfinite(data[col]) | (data[col] < 0), col] = np.nan
    data = data.drop_duplicates()
    assert not data.duplicated(['city', 'time']).any(), 'Trùng mốc giờ nhưng khác giá trị.'
    assert (data.time.dt.minute == 0).all()
    data = data.sort_values(['city', 'time']).reset_index(drop=True)
    return data

hourly = clean_hourly(raw_history)
assert hourly.time.min() == pd.Timestamp('2023-01-01')
assert hourly.time.max() == pd.Timestamp('2026-10-04 23:00')
hourly.to_csv(RUN / 'processed' / 'hourly_clean.csv', index=False)
quality = []
for city, group in hourly.groupby('city'):
    expected = pd.date_range(group.time.min(), group.time.max(), freq='h')
    quality.append({'city': city, 'rows': len(group), 'missing_hours': len(expected.difference(group.time)),
                    'missing_values': int(group[VALUES].isna().sum().sum()),
                    'start': group.time.min(), 'end': group.time.max()})
quality = pd.DataFrame(quality)
quality.to_csv(RUN / 'reports' / 'hourly_quality.csv', index=False)
display(quality)