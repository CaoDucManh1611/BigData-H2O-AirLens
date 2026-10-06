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