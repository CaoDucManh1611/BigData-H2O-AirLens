import os
h2o.init(max_mem_size='3G', nthreads=2)
assert h2o.estimators.H2OXGBoostEstimator.available(), 'Runtime không hỗ trợ XGBoost; cần runtime Linux Colab.'
hframes = {}
for name, part in splits.items():
    hframes[name] = h2o.H2OFrame(part[predictors + ['target_aqi']])
    hframes[name]['city'] = hframes[name]['city'].asfactor()
aml = H2OAutoML(max_models=24, max_runtime_secs=0, max_runtime_secs_per_model=60,
               nfolds=0, seed=42, sort_metric='RMSE', stopping_metric='RMSE',
               project_name='openmeteo_nextday_' + RUN_ID,
               include_algos=None, exclude_algos=None,
               export_checkpoints_dir=str(RUN / 'models' / 'checkpoints'), verbosity='info')
save_json({'max_models': 24, 'max_runtime_secs_per_model': 60, 'nfolds': 0, 'seed': 42,
           'include_algos': None, 'exclude_algos': None, 'selection': 'validation RMSE',
           'blending': 'chronological dedicated split'}, RUN / 'reports' / 'automl_settings.json')
aml.train(x=predictors, y='target_aqi', training_frame=hframes['train'],
          validation_frame=hframes['early_stop'], blending_frame=hframes['blend'],
          leaderboard_frame=hframes['validation'])
leader = aml.leader
leaderboard = get_leaderboard(aml, extra_columns='ALL').as_data_frame()
leaderboard.to_csv(RUN / 'metrics' / 'leaderboard_validation.csv', index=False)
aml.event_log.as_data_frame().to_csv(RUN / 'logs' / 'automl_events.csv', index=False)
save_json(aml.modeling_steps, RUN / 'reports' / 'executed_modeling_steps.json')
def model_family(model_id):
    return model_id.split('_')[0]
leaderboard['family'] = leaderboard.model_id.map(model_family)
coverage = leaderboard.groupby('family').size().rename('models').reset_index()
coverage.to_csv(RUN / 'reports' / 'algorithm_coverage.csv', index=False)
display(coverage, leaderboard)
required = {'GLM','GBM','DRF','XRT','XGBoost','DeepLearning','StackedEnsemble'}
missing = sorted(required - set(coverage.family))
save_json({'required': sorted(required), 'missing': missing}, RUN / 'reports' / 'algorithm_coverage_check.json')
assert not missing, f'Có nhóm chưa tạo được model: {missing}. Xem automl_events.csv, không coi bản này đã đủ nhóm.'
print('Leader được chọn bằng validation:', leader.model_id)