dates = np.array(sorted(dataset.target_date.unique()))
cuts = [0, int(len(dates)*0.6), int(len(dates)*0.7), int(len(dates)*0.8), int(len(dates)*0.9), len(dates)]
split_names = ['train', 'early_stop', 'blend', 'validation', 'test']
splits = {}; split_report = []
for i, name in enumerate(split_names):
    start = cuts[i] + (1 if i else 0)
    chosen_dates = dates[start:cuts[i+1]]
    part = dataset[dataset.target_date.isin(chosen_dates)].reset_index(drop=True)
    assert len(part) > 30 and part.city.nunique() == 3
    splits[name] = part
    part.to_csv(RUN / 'splits' / f'{name}.csv', index=False)
    split_report.append({'split': name, 'rows': len(part), 'input_start': part.input_date.min(),
                         'target_start': part.target_date.min(), 'target_end': part.target_date.max()})
for left, right in zip(split_names, split_names[1:]):
    assert splits[left].target_date.max() < splits[right].input_date.min()
split_report = pd.DataFrame(split_report)
split_report.to_csv(RUN / 'reports' / 'split_ranges.csv', index=False)
display(split_report)
plt.bar(split_report['split'], split_report.rows, color=['#146b77','#39a6a3','#78bbb2','#ecb34b','#d8745b'])
plt.title('Rows in chronological splits'); save_figure('06_split_sizes.png')