# Open-Meteo H2O — 3 thành phố
Run: 20261005_233342_901346
Nguồn: CAMS qua Open-Meteo; dữ liệu mô hình, không phải số đo trạm.
Mục tiêu: AQI trung bình ngày kế tiếp; horizon 1 ngày.
Lịch sử: 01/01/2023 đến 04/10/2026. Forecast lưu riêng, không train/test.
Leader chọn trên validation: StackedEnsemble_AllModels_1_AutoML_1_20261005_163507
Test MAE: 12.1387; RMSE: 15.8011; R2: 0.7924
Các nhóm thực sự đã train: DRF, DeepLearning, GBM, GLM, StackedEnsemble, XGBoost, XRT
So sánh baseline: metrics/baseline.csv. So sánh nhóm: metrics/family_comparison_test.csv.
Raw hash đã kiểm tra lại: nội dung CSV gốc không thay đổi.
Kết quả đo khả năng dự đoán chuỗi CAMS; không chứng minh độ chính xác so với không khí đo thực tế.
Đặc trưng cần ngày đầu vào hoàn tất. Muốn dự đoán 06/10 từ dữ liệu 05/10 phải cập nhật nguồn và xác định giờ chốt.
DeepLearning và giới hạn thời gian từng model có thể làm kết quả thay đổi nhẹ giữa các lần chạy.

EDA update: paired before/after histograms, monthly trend, correlation, full numeric statistics and quality checks. Snapshot has exactly 13 current workflow cells.
