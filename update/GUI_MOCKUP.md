# GUI Mockup - Hệ thống Cập nhật Phần mềm

```
╔════════════════════════════════════════════════════════════════════════════╗
║                   Hệ thống Cập nhật Phần mềm                               ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌─────────────────────────── Cấu hình cập nhật ──────────────────────┐   ║
║  │                                                                      │   ║
║  │  URL Cập nhật:        [_________________________________________]   │   ║
║  │                       (Để trống để tự động phát hiện)               │   ║
║  │                                                                      │   ║
║  │  Thư mục cài đặt:     [________________________________]  [Chọn..] │   ║
║  │                                                                      │   ║
║  │  Phiên bản hiện tại:  [1.0.0_________________________________]      │   ║
║  │                                                                      │   ║
║  │  Thư mục sao lưu:     [________________________________]  [Chọn..] │   ║
║  │                                                                      │   ║
║  │  Tên tiến trình:      [main.exe___________________________]         │   ║
║  │                       (Phân cách bằng dấu phẩy)                     │   ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                            ║
║  ┌─────────────────────────────── Tùy chọn ─────────────────────────────┐  ║
║  │  ☐ Buộc cập nhật         ☐ Chế độ im lặng                           │  ║
║  └──────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║         [Bắt đầu cập nhật]  [Tự động phát hiện]  [Thoát]                  ║
║                                                                            ║
║  ┌────────────────────────── Nhật ký cập nhật ──────────────────────────┐ ║
║  │ [2026-01-23 16:11:07] [INFO] 🚀 Starting Clean Update Manager        │ ║
║  │ [2026-01-23 16:11:08] [INFO] 🔍 Step 1: Checking for updates...     │ ║
║  │ [2026-01-23 16:11:09] [INFO] 📥 Step 2: Downloading update...       │ ║
║  │ [2026-01-23 16:11:15] [INFO] 📦 Step 3: Extracting update...        │ ║
║  │ [2026-01-23 16:11:18] [INFO] 🛑 Step 4: Terminating processes...    │ ║
║  │ [2026-01-23 16:11:20] [INFO] 📦 Step 5: Creating backup...          │ ║
║  │ [2026-01-23 16:11:25] [INFO] 🔄 Step 6: Replacing files...          │ ║
║  │ [2026-01-23 16:11:30] [INFO] ✅ Step 7: Verifying update...         │ ║
║  │ [2026-01-23 16:11:31] [INFO] 🎉 Update successful!                  │ ║
║  │                                                                      │ ║
║  │                                                                 [↕]  │ ║
║  └──────────────────────────────────────────────────────────────────────┘ ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

## Các thành phần GUI

### 1. Tiêu đề cửa sổ
- **Vị trí**: Thanh tiêu đề của cửa sổ
- **Nội dung**: "Hệ thống Cập nhật Phần mềm"

### 2. Khung "Cấu hình cập nhật"
Chứa các trường nhập liệu:
- **URL Cập nhật**: Entry widget để nhập URL (có thể để trống)
- **Thư mục cài đặt**: Entry widget + Button "Chọn..." để browse
- **Phiên bản hiện tại**: Entry widget (mặc định "1.0.0")
- **Thư mục sao lưu**: Entry widget + Button "Chọn..." (tùy chọn)
- **Tên tiến trình**: Entry widget (mặc định "main.exe")

### 3. Khung "Tùy chọn"
Chứa các checkbox:
- **Buộc cập nhật**: Bỏ qua kiểm tra phiên bản
- **Chế độ im lặng**: Giảm thông báo

### 4. Các nút chức năng
- **[Bắt đầu cập nhật]**: Thực hiện cập nhật
- **[Tự động phát hiện]**: Tìm phiên bản mới nhất
- **[Thoát]**: Đóng ứng dụng

### 5. Khung "Nhật ký cập nhật"
- **ScrolledText widget**: Hiển thị log theo thời gian thực
- Tự động cuộn xuống dưới khi có log mới
- Chỉ đọc (read-only)

## So sánh Console vs GUI

| Tính năng | Console | GUI |
|-----------|---------|-----|
| **Nhập URL** | `--update-url` argument | Entry widget + Label |
| **Nhập thư mục** | `--install-dir` argument | Entry widget + Browse button |
| **Hiển thị log** | `print()` to stdout | ScrolledText widget |
| **Xác nhận** | `input("Press Enter...")` | Button "Thoát" |
| **Tự động phát hiện** | Flag `--dry-run` | Button "Tự động phát hiện" |
| **Tiến trình nền** | Blocking | Threading (non-blocking) |
| **Thông báo lỗi** | Print to console | messagebox.showerror() |
| **Thông báo thành công** | Print to console | messagebox.showinfo() |

## Tính năng nổi bật

1. **Không blocking**: Cập nhật chạy trong thread riêng
2. **Real-time logging**: Log hiển thị ngay khi có
3. **User-friendly**: Giao diện trực quan, dễ sử dụng
4. **Giữ nguyên logic**: Sử dụng lại 100% logic từ console version
5. **Validation**: Xác nhận trước khi cập nhật
6. **Browse dialog**: Chọn thư mục dễ dàng
