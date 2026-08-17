# Caro Game

## Archive (đã release)

### Version 2.2

- [x] **Feature: Tự động reset ván sau 6s + xóa nút Chơi Ván Mới**
  - Mô tả: Xóa nút "🔄 Chơi Ván Mới". Sau game_over, hiển thị countdown "Ván mới sau Ns..." (màu cam). Server-side countdown qua `socketio.start_background_task`. Hết 6s → auto reset, X đi trước. Xóa `alert()` popup.
  - Priority: medium | Effort: M
  - Released: v2.2

- [x] **Feature: Hỏi username cho IP mới, lưu vào players.json**
  - Mô tả: Khi IP lần đầu truy cập (chưa có trong `players.json`), hiển thị form nhập username trước khi vào lobby. Sau khi submit, backend ghi IP → username. Các lần sau không hỏi lại.
  - Priority: medium | Effort: M
  - Released: v2.2

- [x] **Feature: Chat box trong phòng**
  - Mô tả: Ô chat đơn giản trong phòng chơi: input text + danh sách tin nhắn. Gửi qua SocketIO event `chat`, broadcast đến tất cả người trong phòng (X, O, spectator). Giới hạn 50 tin nhắn.
  - Priority: low | Effort: M
  - Released: v2.2

### Version 2.1.5

- [x] **Config & stability: ALLOW_SAME_IP toggle + use_reloader=False**
  - Mô tả: (1) Thêm biến hardcode `ALLOW_SAME_IP` — `True` để cùng IP cầm cả X và O (self-test), `False` để chặn trùng IP. (2) Thêm `use_reloader=False` vào `socketio.run()` để tránh spawn tiến trình con orphan khi tắt server.
  - Priority: high | Effort: S
  - Released: v2.1.1

- [x] **Overline rule: check_win chỉ thắng với đúng 5 quân**
  - Mô tả: `check_win()` dùng `len(winning_cells) >= 5` khiến 6+ quân liên tiếp vẫn thắng. Luật Caro chuẩn: chỉ đúng 5 quân mới thắng, 6+ là overline. Sửa `>= 5` → `== 5`.
  - Priority: high | Effort: S
  - Released: v2.1.3

- [x] **Threat detection comprehensive rewrite**
  - Mô tả: Viết lại hoàn toàn `check_threat_pattern` và `detect_threats`. Các lỗi đã sửa: (1) dùng `==` thay `>=` để tôn trọng overline rule, (2) thêm `backward_open2`/`forward_open2` kiểm tra 2 ô trống → loại false positive, (3) quét threat của cả X và O, (4) kiểm tra gap+piece trong Simple/Open Four để tránh overline.
  - Priority: high | Effort: M
  - Released: v2.1.5

### Version 2.1

- [x] **Feature: Cảnh báo đường nguy hiểm (threat detection)**
  - Mô tả: Quét bàn cờ tìm các đường mà chỉ cần đi thêm 1 quân là thắng (5 quân) hoặc tạo thế thắng chắc (Open Four). 5 pattern: Simple Four, Open Four, Broken Four, Open Three, Broken Three. In đậm (font-weight: bold) quân cờ của cả X và O. Overline-aware. Có nút toggle bật/tắt. **v2.1.5**: Viết lại hoàn toàn.
  - Priority: medium | Effort: L
  - Released: v2.1

- [x] **Fix: Chặn cùng IP chiếm 2 slot (X và O)**
  - Mô tả: Backend kiểm tra IP khi join — nếu IP đó đã có người trong phòng (cầm X hoặc O), tab mới chỉ được làm khán giả. **v2.1.1**: Thêm biến hardcode `ALLOW_SAME_IP`.
  - Priority: high | Effort: S
  - Released: v2.1

### Version 2.0

- [x] **Fix: Chuyển lượt khi người chơi disconnect**
  - Mô tả: Khi người chơi đang đến lượt mà disconnect, tự động chuyển lượt cho đối thủ. Tránh treo game vĩnh viễn.
  - Priority: high | Effort: S
  - Released: v2.0

- [x] **Feature: Tự động nhận diện tên người chơi qua IP LAN**
  - Mô tả: Backend lấy IP LAN, map qua `players.json` → tên hiển thị. IP lạ → `Guest_<IP>`.
  - Priority: high | Effort: M
  - Released: v2.0

- [x] **Feature: Danh sách người chơi trong phòng**
  - Mô tả: Hiển thị danh sách người chơi, phân biệt X/O/khán giả. Real-time.
  - Priority: medium | Effort: M
  - Released: v2.0

- [x] **Feature: Hiển thị mã số phiên bản trên giao diện**
  - Mô tả: Hiển thị version ở góc dưới giao diện.
  - Priority: medium | Effort: S
  - Released: v2.0

### Version 1.0

- [x] **Tạo bàn cờ 20x20**
  - Mô tả: `create_empty_board()` tạo bàn cờ BOARD_SIZE x BOARD_SIZE.
  - Priority: high | Effort: S
  - Released: v1.0

- [x] **3 phòng chơi cố định**
  - Mô tả: Phòng 1, 2, 3 khởi tạo sẵn, chọn từ lobby.
  - Priority: high | Effort: S
  - Released: v1.0

- [x] **Phân quân X/O và chế độ khán giả**
  - Mô tả: Vào trước nhận X, vào sau nhận O, thứ 3+ là khán giả.
  - Priority: high | Effort: S
  - Released: v1.0

- [x] **Kiểm tra thắng (luật Caro)**
  - Mô tả: 5 quân liên tiếp + không bị chặn 2 đầu. Đánh dấu đường thắng màu vàng.
  - Priority: high | Effort: M
  - Released: v1.0

- [x] **Đổi lượt và reset ván**
  - Mô tả: X đi trước, luân phiên. Reset làm mới bàn cờ.
  - Priority: high | Effort: S
  - Released: v1.0

- [x] **Xử lý ngắt kết nối cơ bản**
  - Mô tả: Xóa người chơi khỏi phòng khi disconnect.
  - Priority: high | Effort: S
  - Released: v1.0

- [x] **Tự động lấy IP LAN**
  - Mô tả: Hiển thị link để các máy khác truy cập.
  - Priority: medium | Effort: S
  - Released: v1.0

- [x] **Giao diện lobby và bàn cờ**
  - Mô tả: Màn hình chọn phòng, CSS Grid 30px/cell, click đánh cờ, hiệu ứng ô vừa đánh và ô thắng.
  - Priority: high | Effort: L
  - Released: v1.0
