def make_features(daily_table):
    parts = []
    for city, group in daily_table.groupby('city'):
        group = group.sort_values('date').copy()
        features = group[['city', 'date']].rename(columns={'date': 'input_date'})
        features['target_date'] = features.input_date + pd.Timedelta(days=1)
        for col in VALUES + ['aqi_max', 'pm2_5_std']:
            features[f'{col}_today'] = group[col].to_numpy()
        for lag in [1, 2, 3, 7]:
            features[f'aqi_lag_{lag}'] = group.aqi.shift(lag).to_numpy()
        for window in [3, 7]:
            features[f'aqi_mean_{window}'] = group.aqi.rolling(window, min_periods=window).mean().to_numpy()
            features[f'pm2_5_mean_{window}'] = group.pm2_5.rolling(window, min_periods=window).mean().to_numpy()
        features['target_aqi'] = group.aqi.shift(-1).to_numpy()
        features['input_complete'] = ((group.hour_count == 24) & (group.aqi_count == 24)).to_numpy()
        features['weekday'] = features.target_date.dt.dayofweek
        doy = features.target_date.dt.dayofyear
        features['year_sin'] = np.sin(2 * np.pi * doy / 365.25)
        features['year_cos'] = np.cos(2 * np.pi * doy / 365.25)
        parts.append(features)
    return pd.concat(parts, ignore_index=True).sort_values(['target_date', 'city']).reset_index(drop=True)

features_all = make_features(daily)
predictors = [c for c in features_all if c not in ['input_date', 'target_date', 'target_aqi', 'input_complete']]
dataset = features_all.loc[features_all.input_complete & features_all.target_aqi.notna() & features_all.aqi_lag_7.notna()].copy()
assert 'target_aqi' not in predictors and 'target_date' not in predictors
assert ((dataset.target_date - dataset.input_date).dt.days == 1).all()
# Kiểm tra hồi quy: thay giá trị tương lai không làm đổi đặc trưng của ngày trước đó.
probe = daily.copy(); cutoff = pd.Timestamp('2024-06-01')
probe.loc[probe.date > cutoff, VALUES] = 9999
original = features_all.loc[features_all.input_date <= cutoff, predictors].reset_index(drop=True)
changed = make_features(probe).loc[lambda d: d.input_date <= cutoff, predictors].reset_index(drop=True)
pd.testing.assert_frame_equal(original, changed)
dataset.to_csv(RUN / 'features' / 'supervised_next_day.csv', index=False)
save_json({'predictors': predictors, 'target': 'target_aqi', 'horizon_days': 1}, RUN / 'features' / 'schema.json')
display(dataset.head()); print('Dòng dùng train/eval:', len(dataset), '| Đặc trưng:', len(predictors))