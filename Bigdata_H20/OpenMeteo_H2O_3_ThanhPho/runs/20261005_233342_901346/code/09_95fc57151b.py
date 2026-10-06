family_best = leaderboard.sort_values('rmse').drop_duplicates('family').copy()
family_best[['family','model_id','mae','rmse']].to_csv(RUN / 'metrics' / 'best_per_family_validation.csv', index=False)
test = splits['test']
test_rows = [{'family': 'Baseline', 'model_id': 'Persistence', **metrics(test.target_aqi, test.aqi_today)}]
test_predictions = test[['city','input_date','target_date','target_aqi','aqi_today']].copy()
for row in family_best.itertuples():
    model = h2o.get_model(row.model_id)
    pred = model.predict(hframes['test']).as_data_frame()['predict'].to_numpy()
    test_rows.append({'family': row.family, 'model_id': row.model_id, **metrics(test.target_aqi, pred)})
    if model.model_id == leader.model_id:
        test_predictions['prediction'] = pred
test_comparison = pd.DataFrame(test_rows)
test_comparison.to_csv(RUN / 'metrics' / 'family_comparison_test.csv', index=False)
test_predictions['error'] = test_predictions.prediction - test_predictions.target_aqi
test_predictions.to_csv(RUN / 'predictions' / 'test_predictions.csv', index=False)
leader_metrics = metrics(test.target_aqi, test_predictions.prediction)
save_json({'model_id': leader.model_id, 'test': leader_metrics,
           'baseline_test': metrics(test.target_aqi, test.aqi_today),
           'chosen_on': 'validation RMSE; test does not change leader'}, RUN / 'metrics' / 'leader_test.json')
city_metrics = pd.DataFrame([{'city': city, **metrics(g.target_aqi, g.prediction)} for city, g in test_predictions.groupby('city')])
city_metrics.to_csv(RUN / 'metrics' / 'test_by_city.csv', index=False)
display(family_best[['family','mae','rmse']], test_comparison, city_metrics)
print('Test chỉ chấm điểm; không chọn lại leader theo bảng Test.')