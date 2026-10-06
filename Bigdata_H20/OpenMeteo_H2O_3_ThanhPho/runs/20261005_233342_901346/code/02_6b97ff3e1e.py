def save_figure(name):
    plt.tight_layout()
    plt.savefig(RUN / 'figures' / name, dpi=150, bbox_inches='tight')
    plt.show()
    plt.close()

raw_history.describe(include='all').to_csv(RUN / 'reports' / 'before_describe.csv')
missing_before = raw_history.isna().sum().rename('missing')
missing_before.to_csv(RUN / 'reports' / 'before_missing.csv')
display(raw_history.describe(), missing_before.to_frame())
preview = raw_history.assign(time=pd.to_datetime(raw_history.time), city=raw_history.location_id.map(CITY_MAP))
aqi_col = 'us_aqi (USAQI)'
fig, axes = plt.subplots(1, 2, figsize=(14, 4))
missing_before.plot.bar(ax=axes[0], title='Before: missing values')
preview.boxplot(column=aqi_col, by='city', ax=axes[1])
axes[1].set_title('Before: AQI distribution by city')
fig.suptitle('')
save_figure('02_before_missing_boxplot.png')
for city, group in preview.groupby('city'):
    group.set_index('time')[aqi_col].resample('MS').mean().plot(label=city)
plt.title('Before: monthly mean AQI'); plt.ylabel('US AQI'); plt.legend()
save_figure('02_before_monthly_aqi.png')
for city, group in preview.groupby('city'):
    plt.hist(group[aqi_col].dropna(), bins=45, alpha=0.4, label=city)
plt.title('Before: hourly AQI histogram'); plt.legend()
save_figure('02_before_aqi_histogram.png')