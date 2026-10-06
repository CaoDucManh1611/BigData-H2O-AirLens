# AirLens — demo H2O với Open-Meteo

Mở `CHAY_DEMO.cmd`, giữ cửa sổ chạy và truy cập http://127.0.0.1:8766.

- **Dữ liệu đã tải**: chạy MOJO với ngày đầu vào đã có trong dữ liệu, mặc định 04/10 → dự báo 05/10/2026.
- **API hôm nay**: bấm **Cập nhật & dự báo ngày mai**. Demo lấy 14 ngày CAMS/Open-Meteo gần nhất, tạo đúng 21 đặc trưng và chạy model cho ngày kế tiếp.
- Dữ liệu CAMS ngày hôm nay có thể chứa giờ chưa diễn ra: các giá trị đó là ước tính/dự báo của CAMS, không phải số đo trạm. H2O không dùng giá trị AQI ngày mai làm đầu vào.
- Không lấy file dự báo 05–09/10 để làm dữ liệu thực tế chấm điểm. Metrics trên giao diện lấy từ Test đã lưu của Colab.
- Mọi model/CSV trong `OpenMeteo_H2O_3_ThanhPho` chỉ được đọc. Kết quả mới ghi vào `Demo/exports`.
- Java Temurin portable từ Eclipse Adoptium nằm trong `Demo/runtime`, không cài vào hệ thống. Python dùng bản đã có trên máy này; khi chuyển máy, chỉnh đường dẫn trong launcher.

Kiểm tra đầu vào và dự đoán khớp Colab: `python server.py --check`.
Đã đối chiếu 9 mẫu của Test: cả 21 đặc trưng và kết quả MOJO khớp (sai khác dưới 0.00001).

Model: StackedEnsemble_AllModels_1_AutoML_1_20261005_163507.
Nguồn: https://open-meteo.com/en/docs/air-quality-api — ghi công Open-Meteo và CAMS.
AQI trung bình ngày không thay thế đánh giá AQI theo giờ hay quyết định y tế cá nhân.
