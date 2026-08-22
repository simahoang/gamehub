# Changelog

Nhật ký thay đổi theo version. PM agent ghi vào đây khi release.

---

## [v3.1.15] - 2026-08-21

### Changed
- **Layout**: `#info` và `#role` giờ cùng 1 hàng (flex justify-between): info trái, role phải. `#turn-timer` tách thành card riêng fixed bên trái (`#timer-card`, tương tự `#player-list` bên phải).
- **Màu quân cờ**: X → `#e53935` (đỏ tươi), O → `#27ae60` (xanh lá, trở về như trước DaisyUI). Đồng bộ player list.
- `VERSION` = "v3.1.15"

## [v3.1.14] - 2026-08-21

### Fixed
- **Layout shift: nội dung động đẩy bàn cờ nhảy lên xuống**: thêm `min-height` cố định cho `#roomTitle`, `#info`, `#result`, `#turn-timer`, `#role` → dành chỗ trước, không thay đổi chiều cao khi nội dung động thay đổi. Đổi `#turn-timer` từ `display: none` sang `visibility: hidden` để giữ chỗ trong layout flow.

### Changed
- `VERSION` = "v3.1.14"

## [v3.1.13] - 2026-08-21

### Fixed
- **Màn hình đánh cờ bị giật khi đặt quân**: tối ưu CSS (`overflow: auto`, xóa `transition` trên `.cell`, thêm `contain: layout style` trên `#board`) và JS (bọc `updateBoard` DOM writes trong `requestAnimationFrame`) → giảm reflow/jank.
- **3 nút Undo, Đầu hàng, Rời phòng không cân đối**: thêm `btn-sm` đồng bộ kích thước, đổi layout từ `grid` sang `flex justify-center` → căn giữa đều khi nút Đầu hàng ẩn.

### Added
- **Khung bàn cờ nhấp nháy đỏ khi gần hết giờ**: animation `board-urgent` (border-color + box-shadow đỏ) trên `#board-wrapper` khi `turn_seconds <= min(10, roomTurnSeconds * 0.25)`.

### Changed
- `VERSION` = "v3.1.13"

## [v3.1] - 2026-08-21

### Added
- **Nút Undo — xin phép đối thủ đi lại**: người chơi lỡ click nhầm → bấm `↩ Undo` → đối thủ nhận popup confirm → đồng ý → nước cuối bị xoá, trả lượt. Backend: `move_history` + event `undo_request`/`undo_accept`. Frontend: nút tự động ẩn/hiện theo lượt.

### Changed
- `VERSION` = "v3.1"

## [v3.0] - 2026-08-21

### Added
- **UI overhaul DaisyUI**: giao diện hoàn toàn mới dùng DaisyUI + Tailwind CSS. Lobby dạng card với badge trạng thái (`success`/`warning`/`error`), seat panel, board, chat box, player list đều được thiết kế lại hiện đại. Giữ nguyên toàn bộ logic JS/SocketIO.

### Fixed
- **Validate row/col trong handle_move**: thêm `isinstance(row, int)` + `0 <= row/col < BOARD_SIZE` → chặn negative index, out-of-range, type injection từ client.
- **1 IP chỉ được ngồi 1 ghế trên TOÀN bộ phòng**: `handle_sit` quét toàn bộ `rooms` → 1 máy không thể mở nhiều tab ngồi X ở phòng này, O ở phòng khác.
- **Seat panel xếp 1 hàng ngang**: CSS `flex-direction: row` + `flex-wrap: wrap` → Ghế X/O/Đứng lên nằm gọn 1 hàng, không đè nút Đầu hàng.

### Changed
- `VERSION` = "v3.0"
- `ALLOW_SAME_IP` = `False` (chặn trùng IP, phù hợp deploy LAN thật)
- 6 phòng với thời gian đa dạng: Tiêu chuẩn (45s) x3, Siêu nhanh (15s), Không suy nghĩ (5s), Siêu chậm (180s)

## [v2.7.0] - 2026-08-21

### Added
- **Cấu hình thời gian mỗi nước theo từng phòng (per-room `turn_seconds`)**: 4 phòng với thời gian khác nhau:
  - Phòng Nhanh 🔥 30s/nước
  - Phòng Thường 🕐 60s/nước
  - Phòng Chậm 🐢 120s/nước
  - Phòng Tự Do 🐢 180s/nước
- Hiển thị thời gian ở lobby (`"Phòng Nhanh (30s 🔥) — Trống"`) và trong phòng (`roomTitle`)
- Phòng động mới tạo dùng `TURN_SECONDS = 40s` làm fallback

### Changed
- `VERSION` = "v2.7.0"
- Đổi tên phòng: Phòng 1→Nhanh, Phòng 2→Thường, Phòng 3→Chậm, Phòng 4→Tự Do

## [v2.6.4] - 2026-08-21

### Fixed
- **Broken Three false positive — O án ngữ sau đầu hở vẫn bị cảnh báo (regression v2.6.3)**: pattern `_ O _ X X _ X _` bị flag là Broken Three, nhưng thực tế O án ngữ phía sau biến hướng mở rộng trái thành "ngõ cụt" (mở rộng trái → chuỗi 5 quân bị O chặn 2 đầu → không thắng). Sửa: trong nhánh Broken Three (`total == 3`), thêm kiểm tra ô beyond (cách ô mở 1 bước) không được là quân đối thủ. Nếu là đối thủ → không flag. Thêm test case T9-T12 (17/17 PASS).

## [v2.6.3] - 2026-08-21

### Added
- **Đồng hồ đếm ngược (40 giây/nước)**: `TURN_SECONDS=40`, `turn_clock_worker` đếm ngược mỗi nước; hết giờ → người tới lượt **tính thua** (đối thủ thắng); hiển thị đồng hồ `#turn-timer`.

### Fixed
- **Hiển thị tên người thắng**: payload `game_over` thêm `winner_name`; tách khu kết quả `#result` riêng để countdown không ghi đè tên; hiển thị "Tên (quân) THẮNG!" cho thắng thường + đầu hàng + hết giờ.
- **Xóa chat_history khi phòng trống hoàn toàn**: `handle_disconnect` reset chat + bàn khi không còn player nào (kể cả khán giả).
- **Rate-limit chat server-side**: giới hạn 1 tin/giây theo sid + `message[:200]`.
- **Cảnh báo nguy hiểm bỏ sót broken-three sát biên**: pattern `_ _ X X _ X _ |` (2 đầu hở, sát mép) trước không cảnh báo dù lấp gap tạo **Open Four (thắng chắc)** — do điều kiện cũ đòi `open2` (≥2 ô trống). Sửa nhánh "Broken Three" (`total == 3`) theo đúng luật (BA xác nhận): flag khi **cả 2 đầu hở** (`backward_open and gap_end_open`), không flag khi 1 đầu bị O chặn.
- **Cảnh báo nguy hiểm bỏ sót broken-four 1 đầu biên**: pattern `_ O X X _ X X |` (total==4, 1 đầu O + 1 đầu biên) trước không cảnh báo dù lấp gap → **5 quân thắng**. Sửa nhánh "Broken Four" (`total == 4`) dùng logic `opponent_blocks < 2` (đồng bộ `check_win`) thay vì `(backward_open or gap_end_open)` đơn giản.

### Removed
- Nút Bật/Tắt cảnh báo nguy hiểm (threat toggle) — threat luôn hiển thị.


---

## [v2.5] - 2026-08-20

### Fixed
- **Stored XSS (High)**: escape tên người chơi và tin nhắn chat (helper `escapeHtml`) ở chat history, chat realtime, player list; server giới hạn message 200 ký tự.
- **Test infra**: `tests/test_fix.py` dùng đường dẫn tương đối (trước đây hardcode thư mục cũ → test nhầm bản v2.3.1).

### Added
- **Tự động nhả ghế khi ngồi lì (pre-game idle timeout)**: `IDLE_SECONDS=180`, player theo dõi `last_active`; sweeper định kỳ tự `stand` người ngồi không hoạt động khi ván chưa bắt đầu + thông báo `notice`.

### Changed
- `VERSION` = "v2.5"

### Security (hub.py — Hub v1.1, cùng release)
- `POST /set_username`: guard chỉ cho đăng ký lần đầu (`if ip in players: redirect`) + giới hạn 30 ký tự.
- `cors_allowed_origins=[]` (bỏ `"*"`).

---

## [v2.4] - 2026-08-18

### Added
- **Ghế ngồi & đứng lên (seat management)**: bỏ auto-gán quân khi vào phòng — người chơi mặc định ở trạng thái Đứng (khán giả), tự chọn ngồi ghế X/O qua event `sit`/`stand`. Cờ `game_active` khoá ghế khi đang đánh, mở khoá khi ván kết thúc (tới hết auto-reset). Chỉ cho đánh khi đủ 2 người ngồi; đóng tab giữa ván → huỷ ván (không tính thắng). UI hiện 2 ghế (tên người ngồi hoặc "Trống") + nút Ngồi/Đứng.
- **Trạng thái phòng ở Lobby**: lobby render động, hiển thị real-time 3 trạng thái mỗi phòng (`Trống`/`Đang đợi`/`Đầy`) theo số ghế có người ngồi; event `get_rooms` lấy snapshot + broadcast `room_list` khi số người ngồi thay đổi.

### Fixed
- **Guard trạng thái SocketIO handlers**: `handle_reset` chỉ người trong phòng được dùng và chỉ khi `game_over` (không xoá bàn giữa ván); `handle_move`/`handle_surrender` thêm guard `game_over` chống spam trong countdown.
- **Đầu hàng hiển thị đúng người**: payload `game_over` thêm `surrenderer_name`; frontend hiển thị "[người đầu hàng] đã đầu hàng — [người thắng] (piece) THẮNG!" thay vì nhầm người thắng là người đầu hàng.
- **Fix dispatch `get_rooms`**: handler nhận tham số mặc định (`data=None`) + frontend emit `{}` → lobby load được ngay khi mở trang.

### Changed
- `VERSION` = "v2.4"
- Kiểm thử: regression 13/13 PASS + 10/10 luồng mock (seat/sit/stand/move/surrender/reset/disconnect/get_rooms).

---

## [v2.3.1] - 2026-08-17

### Fixed
- **Regression luật thắng**: sửa lại `check_win` — v2.3 đã lỡ bỏ hẳn điều kiện chặn, khiến chuỗi 5 quân bị đối thủ chặn 2 đầu (`O X X X X X O`) vẫn thắng. Luật đúng: thắng khi đúng 5 quân liên tiếp + số đầu bị **quân đối thủ** chặn < 2; biên bàn cờ và ô trống KHÔNG tính là chặn.
- **Threat detection Simple Four**: `O X X X X _ O` không còn bị đánh dấu "đường nguy hiểm" (lấp đầu hở → 5 quân bị đối thủ chặn 2 đầu → không thắng).
- Giữ nguyên các fix đúng của v2.3: biên không chặn (`X X X X X O` thắng, `X X X X _ O` vẫn là threat) và overline (6+ không thắng).

### Changed
- `VERSION` = "v2.3.1"
- Bổ sung test `W5`, `T7`, `T8`; sửa kỳ vọng `W2` (13/13 PASS)

---

## [v2.3] - 2026-08-16

### Fixed
- **Luật thắng**: 5 quân bị chặn 2 đầu vẫn thắng (bỏ điều kiện `blocked_ends < 2`)
- **Threat detection**: Simple Four sát biên `X X X X _ O` giờ là threat (lấp → 5 quân → thắng)
- **Chat lịch sử**: lưu `chat_history` vào room state, giữ nguyên khi refresh/rejoin, chỉ xóa khi phòng trống
- **Đường viền bàn cờ**: `border` + `box-sizing` thay `gap` + `background` → hết artifact 4x4 trên màn hình lớn
- **Chặn zoom**: thêm `maximum-scale=1.0, user-scalable=no`

### Added
- **Nút đầu hàng**: chỉ hiện khi cầm X/O, khi bấm đối thủ thắng, hiển thị "X đã đầu hàng — O THẮNG!"

### Changed
- `VERSION` = "v2.3"

---

## [v2.2.1] - 2026-08-14

### Fixed
- Simple Four false positive: `O X X X X _ O` không còn bị tô đậm (lấp đầu hở → 5 quân bị chặn 2 đầu → không thắng)

---

## [v2.2] - 2026-08-14

### Added
- **Tự động reset ván sau 6s**: sau khi có người thắng, hiển thị countdown "Ván mới sau Ns..." → tự động reset bàn cờ, X đi trước
- **Hỏi username cho IP mới**: form nhập tên hiển thị khi IP lần đầu truy cập, lưu vào `players.json`
- **Chat box trong phòng**: gửi tin nhắn real-time giữa X, O và spectator, giới hạn 50 tin nhắn

### Removed
- Nút "Chơi Ván Mới" (được thay bằng auto-reset)
- `alert()` popup khi thắng (gây khó chịu + chặn UI)

### Changed
- `VERSION` = "v2.2"

---

## [v2.1.5] - 2026-08-14

### Fixed
- **Threat detection rewrite**: viết lại hoàn toàn `check_threat_pattern` và `detect_threats`
  - 5 pattern chính xác: Simple Four, Open Four, Broken Four, Open Three, Broken Three
  - Overline-aware: tất cả điều kiện dùng `==` (không `>=`), bỏ qua pattern dẫn đến 6+ quân
  - Kiểm tra 2 ô trống (`backward_open2`/`forward_open2`) → loại false positive Open/Broken Three
  - Quét threat của cả X và O cùng lúc (không mất threat khi đổi lượt)
  - Kiểm tra gap+piece trong Simple/Open Four → tránh overline (vd: `X _ X X X X O`)
- **Overline rule**: `check_win()` chỉ thắng với đúng 5 quân (`>= 5` → `== 5`), 6+ quân không thắng
- **Config toggle**: biến `ALLOW_SAME_IP` để bật/tắt chặn trùng IP (self-test)
- **Server stability**: `use_reloader=False` tránh orphan process khi tắt server

### Changed
- `VERSION` = "v2.1.5"

---

## [v2.1] - 2026-08-13

### Added
- Cảnh báo đường nguy hiểm (threat detection): 5 pattern, in đậm ký tự X/O trên đường nguy hiểm
- Nút toggle bật/tắt cảnh báo nguy hiểm

### Fixed
- Chặn cùng IP chiếm 2 slot (X và O): mỗi IP chỉ được cầm 1 quân trong 1 phòng

---

## [v2.0] - 2026-08-13

### Added
- Tự động nhận diện tên người chơi qua IP LAN + file `players.json` (map IP → tên)
- Danh sách người chơi trong phòng (real-time), phân biệt X (đỏ), O (xanh), khán giả (xám)
- Hiển thị mã số phiên bản `v2.0` ở góc dưới phải giao diện

### Fixed
- Xử lý chuyển lượt khi người chơi disconnect: không còn treo game vĩnh viễn
  - Người đang đến lượt disconnect → tự động chuyển lượt cho đối thủ
  - Hết người chơi → reset bàn cờ, chờ người mới

---

## [v1.0] - 2026-08-12

### Added
- Bàn cờ 20x20, kích thước tùy chỉnh qua `BOARD_SIZE`
- 3 phòng chơi cố định (Phòng 1, 2, 3)
- Cơ chế phân quân X/O (vào trước nhận X, vào sau nhận O, thứ 3+ là khán giả)
- Kiểm tra thắng theo luật Caro (5 quân liên tiếp, không bị chặn 2 đầu)
- Đường thắng được đánh dấu màu vàng
- Đổi lượt luân phiên (X đi trước), reset ván đấu
- Xử lý ngắt kết nối cơ bản (xóa người chơi khỏi phòng khi disconnect)
- Tự động lấy IP LAN và hiển thị link truy cập
- Giao diện lobby (chọn phòng) và bàn cờ CSS Grid 30px/cell
- Hiệu ứng ô vừa đánh (xanh lá) và ô thắng (vàng)
- Chế độ khán giả (spectator) - xem mà không đánh được