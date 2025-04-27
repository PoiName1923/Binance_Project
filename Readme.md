# Sự án Streaming data với Binance
Dự án thu thập và xử lý dữ liệu thời gian thực từ WebSocket của Binance cho ba loại tiền điện tử: **BTC**, **ETH** và **BNB**.  
Dữ liệu sau đó được chuyển đổi và lưu trữ phục vụ cho các tác vụ phân tích và xây dựng mô hình dự đoán.

## Mục lục
- [Giới thiệu](#giới-thiệu)
- [Sơ đồ](#sơ-đồ)
- [Cách cài đặt](#cách-cài-đặt)
- [Các thư mục](#các-thư-mục)
- [Cách hoạt động](#cách-hoạt-động)
- [Tài Liệu](#tài-liệu-tham-khảo)
## Giới thiệu:
Dự án cá nhân nhằm thực hành xây dựng mô hình **ETL streaming** kết hợp với các công cụ như **Apache Kafka**, **Apache Spark**, và **Airflow**.  
Dữ liệu được thu thập, xử lý theo pipeline thời gian thực, và lưu trữ sau khi xử lý xong hằng ngày.
## Cách cài đặt
1. Clone repo:
   ```bash
   git clone https://github.com/PoiName1923/Binance_Project.git
   cd PROJECT1
2. Khởi động docker:
    ```bash
    docker-compose up -d
## Các thư mục
### dags
Đây là thư mục sẽ đảm nhận nhiệm vụ chạy các tác vụ yêu cầu hằng ngày bằng **Airflow**. Hiện tại chỉ mới có 1 nhiệm vụ duy nhất là thực hiện thu thập dữ liệu theo lô từ Delta Lake (HDFS) và lưu vào Postgres. Có thể mở rộng thêm về việc xây dựng các mô hình dự đoán giá trị crpyto, hoặc các biểu đồ trực quan.
### docker
Chứa các dockerfile mà mình tự xây dựng và các requierments cho từng dockerfile mà mình mong muốn.
### envs 
Chứa cấu hình môi trường của các container trong dự án. Tuy nhiên hạn chế về vấn đề kỹ năng nên phần này mình chỉ cấu hình cho **hadoop**. Các bạn có thể tìm cách đưa toàn bộ **enviroments** của **docker-compose** vào trong phần này và quản lý từng file **.env** riêng biệt.
### initdb
Thư mục này chủ yếu hỗ trợ cho **Postgres**. Dùng để kiểm tra và tạo database cũng như table cần thiết để lưu trữ dữ liệu cuối cùng.
### jars
Chứa các file **.jar** cần thiết cho **Spark** để xử lý dữ liệu và kết nối với các cơ sở dữ liệu cũng như là các công cụ khác.
### Streaming_process
Gồm 2 file đảm nhận quá trình thu thập dữ liệu và xử lý streaming data:
- **spark_process.py**: Xử lý dữ liệu theo lớp kiến trúc Medallion và lưu trữ vào Delta Lake.
### Các file còn lại
- **.gitignore**: chỉ định các file mà git bỏ qua khi push lên github.
- **docker-compose**: chứa toàn bộ container cần thiết.