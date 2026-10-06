model_dir = RUN / 'models' / 'saved'
model_dir.mkdir(exist_ok=True)
saved_models = []
# Chỉ model thuộc lần AutoML này; kèm metalearner cần cho ensemble.
model_ids = set(leaderboard.model_id)
for model_id in list(model_ids):
    model = h2o.get_model(model_id)
    if model.algo == 'stackedensemble':
        model_ids.add(model.metalearner().model_id)
for model_id in sorted(model_ids):
    model = h2o.get_model(model_id)
    saved_models.append({'model_id': model_id, 'path': h2o.save_model(model, path=str(model_dir), force=True)})
save_json(saved_models, RUN / 'models' / 'saved_models.json')
mojo_path = leader.download_mojo(path=str(RUN / 'models'), get_genmodel_jar=True)
save_json({'leader': leader.model_id, 'mojo': mojo_path, 'h2o_version': h2o.__version__,
           'predictors': predictors, 'target': 'next_day_mean_us_aqi'}, RUN / 'models' / 'leader_manifest.json')
latest = features_all.loc[features_all.input_complete].sort_values('input_date').groupby('city').tail(1).copy()
hf_latest = h2o.H2OFrame(latest[predictors]); hf_latest['city'] = hf_latest['city'].asfactor()
latest['h2o_prediction'] = leader.predict(hf_latest).as_data_frame()['predict'].to_numpy()
next_day = latest[['city','input_date','target_date','h2o_prediction']].copy()
next_day['input_source'] = 'Completed historical CAMS day; not station observation'
next_day.to_csv(RUN / 'predictions' / 'next_day_from_completed_history.csv', index=False)
forecast_hourly = clean_hourly(raw_forecast)
forecast_daily = to_daily(forecast_hourly)
forecast_daily.to_csv(RUN / 'processed' / 'source_forecast_daily_SEPARATE.csv', index=False)
display(next_day, forecast_daily[['city','date','aqi']])
print('H2O dự đoán ngày sau ngày lịch sử cuối cùng. AQI 06/10 trong bảng nguồn dự báo là CAMS, không gọi là dự đoán H2O.')