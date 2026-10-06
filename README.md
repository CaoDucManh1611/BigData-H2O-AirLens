# BigData H2O AirLens

Đồ án môn Big Data: dự báo **US AQI trung bình ngày kế tiếp** tại ba tọa độ đại diện cho Hà Nội, Đà Nẵng và TP. Hồ Chí Minh, sử dụng Open-Meteo/CAMS và H2O AutoML.

## Nội dung dự án

- `Demo/`: ứng dụng web AirLens, backend Python và Java portable để suy luận MOJO.
- `OpenMeteo_H2O_3_ThanhPho/`: dữ liệu gốc và kết quả thực nghiệm mà demo đang sử dụng.
- `Bigdata_H20/`: bản tải từ Google Drive, bao gồm ZIP dữ liệu và notebook Colab; giữ nguyên để bảo toàn các file đã tải.
- `Bao_cao_tieu_luan_BigData_H2O_OpenMeteo_AirLens.docx`: báo cáo tiểu luận, hình thực nghiệm và hướng dẫn sử dụng.

Hai thư mục dữ liệu được giữ nguyên theo cấu trúc trên máy. Demo đọc thư mục `OpenMeteo_H2O_3_ThanhPho` ở cấp gốc. File dữ liệu gốc không bị chỉnh sửa khi chuẩn bị repository này.

## Chạy demo trên Windows

Cần Python 3. Java portable đã có trong `Demo/runtime`. Backend demo sử dụng thư viện chuẩn Python.

1. Clone hoặc tải toàn bộ repository vào một đường dẫn không dấu, chẳng hạn `C:\AirLens`.
2. Mở terminal tại thư mục repository và chạy:

```powershell
cd Demo
python -X utf8 server.py
```

3. Truy cập <http://127.0.0.1:8766>.

File `Demo/CHAY_DEMO.cmd` dùng đường dẫn Python của máy triển khai ban đầu. Nếu dùng máy khác, sửa biến `AIR_PYTHON` hoặc chạy lệnh Python ở trên.

### Các chức năng

- **Dữ liệu đã tải:** chọn thành phố và ngày dự báo; sử dụng thông tin ngày liền trước từ dữ liệu đã lưu. Lịch sử hiện kết thúc 04/10/2026, nên dự báo cuối tương ứng 05/10/2026.
- **API hôm nay:** lấy 14 ngày gần nhất từ Open-Meteo, tạo 21 đặc trưng và dự báo ngày kế tiếp. Cần kết nối Internet; nếu API lỗi, đọc thông báo và dùng chế độ dữ liệu đã tải.
- **Tổng quan dữ liệu:** nguồn, thống kê, kiểm tra chất lượng, biểu đồ trước–sau, tương quan, chia tập và kết quả mô hình.
- **Xuất kết quả:** CSV/JSON của demo được ghi vào `Demo/exports`, không ghi đè tập dữ liệu huấn luyện.

Kiểm tra các đặc trưng và dự đoán MOJO khớp với kết quả Colab:

```powershell
cd Demo
python -X utf8 server.py --check
```

## Notebook và quy trình thực nghiệm

Notebook nguồn: `Bigdata_H20/OpenMeteo_H2O_3_ThanhPho.ipynb`. Khi dùng Colab, mount Google Drive và chỉnh `SOURCE_DIR` theo vị trí ZIP dữ liệu của bạn. Các đường dẫn Drive thuộc máy/tài khoản triển khai ban đầu cần được kiểm tra khi chuyển tài khoản.

Quy trình gồm 13 bước, đánh số 0–12: thiết lập tự lưu; đọc nguồn; EDA trước; làm sạch giờ; tổng hợp ngày và EDA sau; đặc trưng và nhãn; chia theo thời gian; baseline; AutoML; đánh giá test; phân tích lỗi; xuất model; xác minh kết quả.

Trong mỗi `runs/<run_id>` có code, log, processed, features, splits, metrics, predictions, figures, reports, notebooks và models. Các file trong `code` là lịch sử ô đã chạy; không chạy toàn bộ lịch sử theo thứ tự tên file. Sử dụng notebook và kiểm tra snapshot tương ứng với lần thực nghiệm cần tái hiện.

## Dữ liệu và kết quả

- Nguồn: [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api), sử dụng đầu ra mô hình khí quyển CAMS.
- Lịch sử: 01/01/2023–04/10/2026; 98.856 dòng giờ, tổng hợp thành 4.119 dòng ngày–thành phố.
- Tập dự báo nguồn 05–09/10/2026 được giữ riêng, không dùng làm nhãn thực tế để chấm test.
- Run dùng trong demo: `20261005_233342_901346`.
- AutoML mở các họ hỗ trợ; đã thử 24 model nền và hai StackedEnsemble. Chọn leader bằng validation, đánh giá trên test tách theo thời gian.

| Mô hình | MAE test | RMSE test | R² test |
| --- | ---: | ---: | ---: |
| Baseline persistence | 15,2793 | 20,8134 | 0,6399 |
| StackedEnsemble AllModels | 12,1387 | 15,8011 | 0,7924 |

## Phạm vi sử dụng

Dữ liệu CAMS là dữ liệu mô hình khí quyển, không phải số đo từ trạm quan trắc. Ba tọa độ không đại diện cho mọi quận trong thành phố. Giá trị trung bình US AQI theo giờ của một ngày không đồng nhất với cách tính AQI ngày chính thức. Kết luận ngoài trời trong demo là gợi ý tham khảo từ ngưỡng AQI, không phải bảo đảm an toàn sức khỏe.

Repository có cả dữ liệu, model nhị phân và Java portable để giữ đủ bộ dự án đã triển khai, nên dung lượng tải lớn hơn một repository chỉ chứa mã nguồn. Các thành phần bên thứ ba giữ giấy phép/ghi công riêng; việc công khai repository không thay đổi giấy phép của chúng.

Tham khảo: [H2O AutoML](https://docs.h2o.ai/h2o/latest-stable/h2o-docs/automl.html), [Open-Meteo](https://open-meteo.com/), [CAMS](https://atmosphere.copernicus.eu/), [Eclipse Adoptium](https://adoptium.net/), [AirNow AQI](https://www.airnow.gov/aqi/aqi-basics/).
