def metrics(y, pred):
    y = np.asarray(y, dtype=float); pred = np.asarray(pred, dtype=float)
    assert len(y) == len(pred) and np.isfinite(y).all() and np.isfinite(pred).all()
    return {'mae': float(mean_absolute_error(y, pred)), 'rmse': float(np.sqrt(mean_squared_error(y, pred))), 'r2': float(r2_score(y, pred))}
baseline_rows = []
for name in ['validation', 'test']:
    frame = splits[name]
    baseline_rows.append({'split': name, 'model': 'Persistence: AQI tomorrow = today', **metrics(frame.target_aqi, frame.aqi_today)})
baseline_results = pd.DataFrame(baseline_rows)
baseline_results.to_csv(RUN / 'metrics' / 'baseline.csv', index=False)
display(baseline_results)