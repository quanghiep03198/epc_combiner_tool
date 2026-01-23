# Hệ thống Cập nhật Phần mềm - Phiên bản GUI

## Mô tả

Ứng dụng cập nhật phần mềm EPC với giao diện đồ họa sử dụng Tkinter. Đây là phiên bản GUI của `update_manager.py`, giữ nguyên toàn bộ logic xử lý cập nhật nhưng thay thế giao diện console bằng giao diện đồ họa thân thiện.

## Tính năng

- ✅ Giao diện đồ họa trực quan với Tkinter
- ✅ Tự động phát hiện phiên bản mới nhất từ GitHub
- ✅ Hiển thị nhật ký cập nhật theo thời gian thực
- ✅ Hỗ trợ cấu hình các tham số cập nhật
- ✅ Chạy cập nhật trong luồng nền, không đóng băng giao diện
- ✅ Giữ nguyên toàn bộ logic xử lý từ phiên bản console

## Yêu cầu

- Python 3.7 trở lên
- Tkinter (thường được cài sẵn với Python)
- Các thư viện khác từ `requirements.txt`

## Cách sử dụng

### Khởi chạy ứng dụng

```bash
python update/update_manager_gui.py
```

### Giao diện chính

Cửa sổ chính bao gồm:

1. **Cấu hình cập nhật**:
   - URL Cập nhật: URL tải xuống phiên bản mới (có thể để trống để tự động phát hiện)
   - Thư mục cài đặt: Đường dẫn thư mục cài đặt phần mềm
   - Phiên bản hiện tại: Phiên bản đang sử dụng
   - Thư mục sao lưu: Nơi lưu bản sao lưu (tùy chọn)
   - Tên tiến trình: Các tiến trình cần đóng trước khi cập nhật

2. **Tùy chọn**:
   - Buộc cập nhật: Bỏ qua kiểm tra phiên bản
   - Chế độ im lặng: Giảm thông báo

3. **Các nút chức năng**:
   - Bắt đầu cập nhật: Bắt đầu quá trình cập nhật
   - Tự động phát hiện: Tìm và điền URL phiên bản mới nhất
   - Thoát: Đóng ứng dụng

4. **Nhật ký cập nhật**: Hiển thị quá trình cập nhật chi tiết

## So sánh với phiên bản Console

### Phiên bản Console (`update_manager.py`)
```python
# Chạy từ dòng lệnh với tham số
python update_manager.py --update-url <URL> --install-dir "." --force
```

### Phiên bản GUI (`update_manager_gui.py`)
```python
# Chạy và điều khiển qua giao diện
python update_manager_gui.py
```

## Kiến trúc

```
update_manager_gui.py
├── UpdateManagerGUI (Giao diện Tkinter)
│   ├── create_widgets() - Tạo các thành phần GUI
│   ├── auto_detect_release() - Tự động phát hiện phiên bản
│   ├── start_update() - Bắt đầu cập nhật
│   └── append_log() - Hiển thị nhật ký
└── Sử dụng CleanUpdateManager từ update_manager.py
```

## Thay đổi từ Console sang GUI

1. **Thay thế print()**: 
   - Console: `print("Message")`
   - GUI: `self.append_log("Message")`

2. **Thay thế input()**:
   - Console: `input("Press Enter to exit...")`
   - GUI: Sử dụng nút "Thoát"

3. **Thay thế argparse**:
   - Console: Tham số dòng lệnh
   - GUI: Các ô nhập liệu (Entry) và nút (Button)

4. **Thêm threading**:
   - Chạy cập nhật trong luồng nền để không đóng băng GUI

## Lưu ý

- Ứng dụng GUI giữ nguyên toàn bộ logic xử lý từ `update_manager.py`
- Nhật ký cũng được ghi vào file `logs/update.log` như phiên bản console
- Có thể chạy cả hai phiên bản (console và GUI) tùy theo nhu cầu
