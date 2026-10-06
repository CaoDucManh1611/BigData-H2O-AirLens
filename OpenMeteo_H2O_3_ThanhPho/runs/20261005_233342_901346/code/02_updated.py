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
# Pearson correlation of original hourly values (no cleaning or aggregation).
raw_corr_columns = ['pm10 (μg/m³)', 'pm2_5 (μg/m³)', 'carbon_monoxide (μg/m³)', 'nitrogen_dioxide (μg/m³)', 'sulphur_dioxide (μg/m³)', 'ozone (μg/m³)', 'us_aqi (USAQI)']
raw_corr_labels = ['pm10', 'pm2_5', 'co', 'no2', 'so2', 'o3', 'aqi']
before_corr = raw_history[raw_corr_columns].corr(method='pearson')
before_corr.index = raw_corr_labels
before_corr.columns = raw_corr_labels
assert before_corr.shape == (7, 7)
assert np.allclose(before_corr, before_corr.T, equal_nan=True)
before_corr.to_csv(RUN / 'reports' / 'before_correlation.csv')
fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(before_corr, vmin=-1, vmax=1, cmap='coolwarm')
ax.set_xticks(range(7), raw_corr_labels, rotation=45)
ax.set_yticks(range(7), raw_corr_labels)
fig.colorbar(im, ax=ax)
ax.set_title('Before: original hourly feature correlation')
save_figure('02_before_correlation.png')
print('SAVED: before_correlation.csv and 02_before_correlation.png', RUN)
