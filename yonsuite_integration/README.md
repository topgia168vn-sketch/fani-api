# YonSuite Integration Module

## Mô tả
Module tích hợp với YonSuite API để quản lý access token và đồng bộ hóa đơn hàng.

## Tính năng

### 1. Quản lý API Configuration
- Cấu hình thông tin API trực tiếp trong Settings (Base URL, App Key, App Secret)
- Lưu trữ access token và thông tin liên quan
- Test kết nối API

### 2. Quản lý Access Token
- Lấy access token thủ công qua button "Get Access Token"
- Tự động refresh token mỗi 5 phút thông qua cron job
- Hiển thị thời gian hết hạn của token
- Theo dõi số lần refresh token và thời gian refresh cuối

### 3. Quản lý YonSuite Products
- Tạo và quản lý sản phẩm YonSuite
- Button "Sync to YonSuite" để đồng bộ sản phẩm lên API
- Test API sản phẩm trực tiếp từ Settings
- Theo dõi trạng thái đồng bộ hóa

### 4. Quản lý YonSuite Sale Orders
- Tạo và quản lý đơn hàng YonSuite
- Button "Push to YonSuite" để gửi đơn hàng lên API
- Theo dõi trạng thái đồng bộ hóa
- Xử lý lỗi đồng bộ hóa

## Cài đặt

1. Copy module vào thư mục addons
2. Cập nhật danh sách apps: Apps > Update Apps List
3. Tìm và cài đặt module "YonSuite Integration"

## Cấu hình

1. Vào Settings > YonSuite Integration
2. Điền thông tin cấu hình:
   - **YonSuite Base URL**: `https://c1.yonyoucloud.com/iuap-api-auth`
   - **YonSuite App Key**: Key từ YonSuite
   - **YonSuite App Secret**: Secret từ YonSuite
3. Click "Get Access Token" để lấy token đầu tiên
4. Click "Test Connection" để kiểm tra kết nối

## Sử dụng

### Cấu hình API
1. Vào Settings > YonSuite Integration
2. Điền đầy đủ thông tin API credentials
3. Sử dụng button "Get Access Token" và "Test Connection" để kiểm tra
4. Token sẽ được tự động refresh mỗi 5 phút

### Quản lý YonSuite Products
1. Vào menu YonSuite Integration > Products
2. Tạo sản phẩm mới với tên, mã, giá
3. Click "Sync to YonSuite" để đồng bộ lên API
4. Test API sản phẩm từ Settings > YonSuite API > "Test Product API"

### Tạo YonSuite Sale Order
1. Vào menu YonSuite Integration > Sale Orders
2. Tạo đơn hàng mới với tên và mô tả
3. Click "Push to YonSuite" để gửi lên API

### Cron Job
- Cron job tự động chạy mỗi 5 phút
- Kiểm tra token có sắp hết hạn không (trong vòng 10 phút)
- Tự động lấy token mới nếu cần

## Cấu trúc Module

```
yonsuite_integration/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── yonsuite_api.py           # Service class chứa phương thức API
│   ├── res_config_settings.py    # Cấu hình settings và quản lý token
│   ├── yonsuite_product.py       # Model sản phẩm YonSuite
│   └── yonsuite_sale_order.py    # Model đơn hàng YonSuite
├── views/
│   ├── res_config_settings_views.xml  # View cấu hình settings
│   ├── yonsuite_product_views.xml     # Views sản phẩm
│   └── yonsuite_sale_order_views.xml  # Views đơn hàng
├── security/
│   └── ir.model.access.csv       # Quyền truy cập
├── data/
│   └── cron_data.xml            # Cron job tự động refresh token
└── README.md
```

## API Integration

Module sử dụng logic tương tự như file `yonsuite.py`:
- HMAC-SHA256 signature
- Base64 encoding
- URL encoding
- GET request với query parameters

## Kiến trúc

- **`yonsuite.api`**: TransientModel chứa các phương thức gọi API (service class)
- **`res.config.settings`**: Lưu trữ cấu hình API và access token
- **`yonsuite.product`**: Model quản lý sản phẩm YonSuite
- **`yonsuite.sale.order`**: Model quản lý đơn hàng YonSuite

## Lưu ý

- Tất cả cấu hình API được lưu trong `ir.config_parameter`
- Cron job sử dụng `res.config.settings` để refresh token
- Button "Push to YonSuite" hiện tại chỉ là placeholder, cần implement logic thực tế
- `yonsuite.api` là service class không lưu trữ dữ liệu, chỉ chứa logic gọi API
