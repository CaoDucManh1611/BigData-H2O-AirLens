def to_daily(data):
    temp = data.assign(date=data.time.dt.normalize())
    grouped = temp.groupby(['city', 'date'])
    means = grouped[VALUES].mean()
    counts = grouped[VALUES].count().add_suffix('_count')
    daily_table = means.join(counts)
    daily_table['hour_count'] = grouped.size()
    daily_table['aqi_max'] = grouped.aqi.max()
    daily_table['pm2_5_std'] = grouped.pm2_5.std()
    # Ngày thiếu giờ/thiếu AQI không được dùng làm nhãn; giữ dòng để lag không nhảy qua ngày thiếu.
    daily_table.loc[(daily_table.hour_count != 24) | (daily_table.aqi_count != 24), 'aqi'] = np.nan
    result = []
    for city, group in daily_table.reset_index().groupby('city'):
        group = group.set_index('date').reindex(pd.date_range(group.date.min(), group.date.max(), freq='D'))
        group.index.name = 'date'
        group['city'] = city
        result.append(group.reset_index())
    return pd.concat(result, ignore_index=True).sort_values(['city', 'date']).reset_index(drop=True)

daily = to_daily(hourly)
daily.to_csv(RUN / 'processed' / 'daily_clean.csv', index=False)
daily.describe(include='all').to_csv(RUN / 'reports' / 'after_daily_describe.csv')
display(daily.groupby('city')[VALUES].agg(['count', 'mean', 'std', 'min', 'max']))
fig, axes = plt.subplots(1, 2, figsize=(14, 4))
daily[VALUES].isna().sum().plot.bar(ax=axes[0], title='After: daily missing values')
daily.boxplot(column='aqi', by='city', ax=axes[1]); axes[1].set_title('After: daily mean AQI')
fig.suptitle(''); save_figure('04_after_missing_boxplot.png')
for city, group in daily.groupby('city'):
    plt.plot(group.date, group.aqi, label=city, alpha=0.7, linewidth=0.8)
plt.title('After: daily mean AQI over time'); plt.ylabel('US AQI'); plt.legend()
save_figure('04_after_daily_aqi.png')
corr = daily[VALUES].corr()
fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(corr, vmin=-1, vmax=1, cmap='coolwarm')
ax.set_xticks(range(len(VALUES)), VALUES, rotation=45); ax.set_yticks(range(len(VALUES)), VALUES)
fig.colorbar(im, ax=ax); ax.set_title('After: daily feature correlation')
save_figure('04_after_correlation.png')
# Paired EDA: same bins, units, time resolution and axis limits.
raw_numeric = raw_history[list(RENAME)].apply(pd.to_numeric, errors='coerce')
raw_numeric.columns = VALUES
quality_rows = []
for stage, data, keys in [('before_hourly', raw_history, ['location_id','time']), ('after_hourly', hourly, ['city','time']), ('after_daily', daily, ['city','date'])]:
    numeric = raw_numeric if stage == 'before_hourly' else data[VALUES]
    numeric = numeric.apply(pd.to_numeric, errors='coerce')
    quality_rows.append({'stage': stage, 'rows': len(data), 'missing_original_cells': int(data[list(RENAME) if stage == 'before_hourly' else VALUES].isna().sum().sum()), 'missing_numeric_cells': int(numeric.isna().sum().sum()), 'negative_cells': int((numeric < 0).sum().sum()), 'infinite_cells': int(np.isinf(numeric.to_numpy(dtype=float)).sum()), 'duplicate_keys': int(data.duplicated(keys).sum())})
quality_comparison = pd.DataFrame(quality_rows)
quality_comparison.to_csv(RUN / 'reports' / 'quality_before_after.csv', index=False)
after_corr = daily[VALUES].corr(method='pearson')
after_corr.to_csv(RUN / 'reports' / 'after_correlation.csv')
raw_numeric.describe().to_csv(RUN / 'reports' / 'before_numeric_describe.csv')
daily[VALUES].describe().to_csv(RUN / 'reports' / 'after_numeric_describe.csv')
all_aqi = pd.concat([raw_numeric.aqi, daily.aqi]).replace([np.inf, -np.inf], np.nan).dropna()
common_bins = np.linspace(all_aqi.min(), all_aqi.max(), 46)
fig, axes = plt.subplots(1, 2, figsize=(14, 4), sharex=True, sharey=True)
for ax, data, title in [(axes[0], raw_history.assign(city=raw_history.location_id.map(CITY_MAP), aqi=raw_numeric.aqi), 'Before: hourly AQI density'), (axes[1], daily, 'After: daily mean AQI density')]:
    for city, group in data.groupby('city'):
        ax.hist(group.aqi.dropna(), bins=common_bins, density=True, alpha=0.4, label=city)
    ax.set(title=title, xlabel='US AQI', ylabel='Probability density')
    ax.legend()
save_figure('04_before_after_aqi_histogram.png')
raw_monthly = raw_history.assign(city=raw_history.location_id.map(CITY_MAP), time=pd.to_datetime(raw_history.time), aqi=raw_numeric.aqi).set_index('time').groupby('city').aqi.resample('MS').mean()
# Weight daily means by hourly counts so monthly aggregation remains comparable.
daily_monthly = daily.assign(month=daily.date.dt.to_period('M').dt.to_timestamp(), weighted=daily.aqi*daily.aqi_count).groupby(['city','month']).agg(total=('weighted','sum'), count=('aqi_count','sum'))
daily_monthly['aqi'] = daily_monthly.total / daily_monthly['count']
fig, axes = plt.subplots(1, 2, figsize=(14, 4), sharex=True, sharey=True)
for city in sorted(CITY_MAP.values()):
    raw_monthly.loc[city].plot(ax=axes[0], label=city)
    daily_monthly.loc[city].aqi.plot(ax=axes[1], label=city)
for ax, title in zip(axes, ['Before: monthly AQI from hourly raw', 'After: monthly AQI from daily means']):
    ax.set(title=title, xlabel='Month', ylabel='Mean US AQI'); ax.legend()
save_figure('04_before_after_monthly_aqi.png')
assert len(quality_comparison) == 3
assert sum(quality_comparison.duplicate_keys) == 0
assert before_corr.columns.tolist() == after_corr.columns.tolist()
assert np.allclose(np.diag(after_corr), 1)
display(quality_comparison)
print('PAIRED EDA SAVED: histogram, monthly trend, numeric statistics, quality audit, correlation CSV.')
