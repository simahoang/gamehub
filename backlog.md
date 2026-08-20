# Backlog

Nguồn sự thật duy nhất cho toàn bộ dự án. PM agent là người đọc/ghi file này.

## Cách dùng

- Mỗi feature có trạng thái: `[ ]` (todo), `[~]` (in progress), `[x]` (done), `[!]` (blocked).
- Mỗi item ghi: tên, mô tả, priority, effort, version mục tiêu.
- **Priority**: `high` (gấp), `medium` (bình thường), `low` (thấp).
- **Effort** (độ lớn): `S` (<1h), `M` (1-3h), `L` (3-8h), `XL` (>8h).

---

# Hub

## Version 1.0 (đã release)

- [x] **Kiến trúc Hub: migrate Caro thành module, thêm trang chọn game**
  - Mô tả: Tạo `hub.py` làm entry point Flask + SocketIO. Refactor `caro_web.py` → `caro_game.py` (module, không tự chạy). Trang chủ `/` hiển thị các ô chọn game (Caro, Pet...). Mỗi game mount vào route riêng (`/caro`, `/pet`). Chung `players.json` ở gốc workspace.
  - Priority: high | Effort: M
  - Released: Hub v1.0

- [x] **Data architecture: IP làm key chính, players.json trung tâm ở gốc**
  - Mô tả: Move `players.json` từ `caro-game/` ra gốc workspace → **identity trung tâm**: `IP → {name, created_at}`. IP là key chính xuyên suốt mọi game (không trùng tên, không cần login). Mỗi game có file data riêng key theo IP: Caro → `caro_data.json` (ELO/stats), Pet → `pets.json`. Refactor Caro để đọc `players.json` từ gốc, bỏ cấu trúc flat string cũ.
  - Priority: high | Effort: M
  - Released: Hub v1.0

- [x] **Feature: Chuyển flow "hỏi username lần đầu" từ Caro sang Hub**
  - Mô tả: Hiện tại việc hỏi username khi IP lần đầu truy cập nằm trong Caro (`/set_username`). Chuyển lên Hub chính: khi user vào trang chủ `/` lần đầu (IP chưa có trong `players.json` gốc), hiện form nhập tên → ghi vào `players.json` gốc. Sau đó các game (Caro, Pet) đọc tên từ identity trung tâm, không tự hỏi lại. Xóa flow `/set_username` cũ trong Caro.
  - Priority: high | Effort: M
  - Released: Hub v1.0

## Version 1.1 (đang lên kế hoạch)

- [ ] **Feature: Phản hồi (Feedback) — dùng chung cho mọi game**
  - Mô tả: Thêm cơ chế gửi phản hồi/lỗi dạng free text cho người chơi. Server lưu lại kèm IP, username và **phân theo game** (game_id). Tất cả game hiện tại (Caro, Pet) và game tương lai đều có tính năng này. Backend: route/event chung nhận feedback → ghi file `feedback.json` (hoặc từng file theo game), mỗi entry: `{game, ip, username, message, created_at}`. Frontend: nút "Gửi phản hồi" trong giao diện mỗi game (có thể là modal/form nhỏ).
  - Priority: medium | Effort: M
  - Version: Hub v1.9

- [x] **Fix (bảo mật): Chặn tái gửi username cho IP đã tồn tại**
  - Mô tả: Endpoint `POST /set_username` (hub.py) KHÔNG kiểm tra IP đã có trong `players.json` → ai cũng có thể ghi đè tên + reset `created_at` của chính IP mình bằng Postman/curl/devtools. Thêm guard `if ip in players: return redirect('/')` (chỉ cho đăng ký lần đầu), KHÔNG ghi đè `created_at` khi tái gửi; xem xét giới hạn độ dài tên + chống CSRF.
  - Priority: high | Effort: S
  - Version: Hub v1.1
  - Released: Hub v1.1

- [x] **Fix (bảo mật): Thu hẹp `cors_allowed_origins`**
  - Mô tả: `cors_allowed_origins="*"` (hub.py:17) cho phép site độc trong LAN mở kết nối socket.io đến server rồi emit `join/move/chat/surrender` thay cho nạn nhân (IP là IP nạn nhân). Giới hạn về origin tin cậy (hoặc same-origin), xem xét thêm token handshake.
  - Priority: medium | Effort: S
  - Version: Hub v1.1
  - Released: Hub v1.1

---

# Caro Game

## Version 2.3 (đã release)

- [x] **Fix: Luật thắng — 5 quân bị chặn 2 đầu vẫn thắng**
  - Mô tả: `X X X X X O` (5 quân, biên trái + O chặn phải) — hiện tại `blocked_ends = 2` → không thắng. Sửa `check_win`: bỏ `blocked_ends < 2`, chỉ giữ `len(winning_cells) == 5`. Đồng thời sửa threat detection Simple Four: bỏ kiểm tra blocker 2 ô.
  - Priority: high | Effort: M
  - Released: v2.3

- [x] **Fix: Chat box lưu lịch sử khi refresh/rejoin**
  - Mô tả: Chat hiện chỉ lưu trong DOM frontend, mất khi refresh hoặc spectator join sau. Lưu `chat_history` (list 50 tin nhắn gần nhất) vào room state. Gửi kèm trong `init` event khi join. Chỉ xóa khi phòng trống hoàn toàn.
  - Priority: medium | Effort: S
  - Released: v2.3

- [x] **Fix: Đường viền đen đậm không đều ở mỗi cụm 4x4 trên màn hình lớn**
  - Mô tả: Board dùng `gap: 1px` + `background: #000` tạo đường kẻ. Trên màn hình lớn/high-DPI, browser làm tròn sub-pixel không đều → pattern 4x4. Thay bằng `border: 1px solid #000` + `box-sizing: border-box` trên `.cell`, set `gap: 0; background: transparent` trên `#board`.
  - Priority: medium | Effort: S
  - Released: v2.3

- [x] **Feature: Nút đầu hàng**
  - Mô tả: Thêm nút "Đầu hàng" trong game controls. Chỉ hiển thị khi cầm X hoặc O (không hiện với spectator). Khi bấm → emit `surrender` → đối thủ thắng, trigger countdown reset.
  - Priority: medium | Effort: S
  - Released: v2.3

- [x] **Fix: Chặn phóng to/thu nhỏ trình duyệt làm vỡ giao diện**
  - Mô tả: Thêm `<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">` để chặn zoom. Bọc bàn cờ trong container `overflow: auto` để có scrollbar khi vượt kích thước màn hình.
  - Priority: medium | Effort: S
  - Released: v2.3

## Version 2.3.1 (đã release)

- [x] **Fix: Regression v2.3 — 5 quân bị đối thủ chặn 2 đầu lại thắng**
  - Mô tả: v2.3 bỏ hẳn `blocked_ends < 2` trong `check_win` khiến MỌI chuỗi đúng 5 quân đều thắng, kể cả bị đối thủ chặn 2 đầu (`O X X X X X O`) và threat detection Simple Four đánh dấu nhầm `O X X X X _ O`. Yêu cầu đúng của v2.3 chỉ là **biên bàn cờ (out of bounds) không tính là chặn**; quân đối thủ vẫn chặn. Luật đúng: thắng khi đúng 5 quân liên tiếp + số đầu bị **quân đối thủ** chặn < 2 (biên/ô trống không tính chặn). Sửa `check_win` + thêm điều kiện chặn 2 đầu cho Simple Four.
  - Priority: high | Effort: S
  - Version: v2.3.1
  - Released: v2.3.1

## Version 2.4 (đã release)

- [x] **Feature: Ghế ngồi & đứng lên (seat management)**
  - Mô tả: Bỏ cơ chế auto-gán quân khi join. Người chơi vào phòng mặc định ở trạng thái **Đứng** (khán giả), tự chọn ngồi vào ghế X hoặc O. Thêm 2 event `sit`(`room`,`piece`) và `stand`(`room`). Thêm cờ `game_active` để khoá ghế: khoá nút Ngồi/Đứng khi đang đánh (`game_active=True`), mở khoá khi ván kết thúc (thắng/đầu hàng) cho tới hết auto-reset. Luật chuyển trạng thái: `False→True` khi có nước đi đầu tiên (đủ 2 người ngồi, X hạ quân); `True→False` khi thắng/đầu hàng/hủy ván. Chỉ cho `move` khi đủ 2 người ngồi. Giữ luật 1 IP 1 ghế (`ALLOW_SAME_IP`). Đóng tab giữa ván → huỷ ván (reset bàn, không tính thắng), giải phóng ghế. UI: hiện 2 ghế (tên người ngồi hoặc "Trống") + nút Ngồi/Đứng lên.
  - Priority: high | Effort: M
  - Version: v2.4
  - Released: v2.4

- [x] **Feature: Hiển thị trạng thái phòng ở Lobby**
  - Mô tả: Lobby hiện là 3 nút tĩnh, không biết phòng nào còn chỗ. Hiển thị real-time mỗi phòng với **3 trạng thái** dựa trên số ghế có người ngồi (piece X/O): `Trống` (0 ghế), `Đang đợi` (1 ghế), `Đầy` (2 ghế). Không hiện tên người chơi, không ghi chi tiết ghế X/O, không hiện số khán giả. Backend: hàm `get_rooms_summary()` (trả số ghế đã ngồi mỗi phòng) + broadcast `room_list` mỗi khi số người ngồi đổi (sit/stand/disconnect; hoặc join nếu còn cơ chế auto-sit). Frontend: lobby render nút phòng động, emit `get_rooms` khi mở để lấy snapshot ban đầu, nghe `room_list` tự cập nhật không cần F5. Phòng `Đầy` vẫn bấm vào để vào làm khán giả.
  - Priority: medium | Effort: S
  - Version: v2.4
  - Released: v2.4

- [x] **Fix: Xác thực & guard trạng thái các SocketIO handler (thay cho "Chống spam click")**
  - Mô tả: Rate-limit nước đi là thừa — luật luân phiên `piece == turn` (đảo lượt sau mỗi nước) + kiểm tra ô trống đã giới hạn mỗi người 1 nước/lượt. Thay vào đó sửa 2 lỗ hổng thật: (1) `handle_reset` không kiểm tra `request.sid` → bất kỳ ai cũng emit `reset` xoá bàn giữa ván (thêm check sid trong phòng / chỉ khi `game_over`); (2) `handle_move` và `handle_surrender` thiếu guard `game_over` → trong 6s countdown người thắng vẫn emit thêm nước / spam surrender sinh nhiều background task `countdown_worker` song song (thêm `if r_data.get('game_over'): return` đầu hàm).
  - Priority: low | Effort: S
  - Version: v2.4
  - Released: v2.4

- [x] **Fix: Đầu hàng hiển thị đúng người đã đầu hàng**
  - Mô tả: Khi đầu hàng, payload `game_over` chỉ gửi `winner_name` (tên người thắng), còn frontend (dòng 320) ghép `winner_name + ' đã đầu hàng'` → hiển thị nhầm người thắng là người đầu hàng, không biết ai bấm. Sửa backend (`handle_surrender`): thêm `surrenderer_name = players[request.sid]['name']` vào emit. Sửa frontend: `msg = surrenderer_name + ' đã đầu hàng — ' + winner_name + ' (' + winner + ') THẮNG!'` (vd: "Hoang đã đầu hàng — Dung (O) THẮNG!").
  - Priority: medium | Effort: S
  - Version: v2.4
  - Released: v2.4

- [x] **Fix: Đếm ngược không khớp (5s thực tế vs 8s cấu hình)**
  - Mô tả: `COUNTDOWN_SECONDS = 8` nhưng `countdown_worker` đếm `range(5, -1, -1)` (5→0). Đồng bộ về 1 giá trị duy nhất (dùng `COUNTDOWN_SECONDS`), trả 0 nháy cuối trước auto-reset. Pre-existing, ngoài scope v2.4.
  - Priority: low | Effort: S

## Caro Waiting

- [x] **Fix (bảo mật HIGH): Stored XSS qua tên người chơi & tin nhắn chat**
  - Mô tả: Tên (từ `players.json`) và tin nhắn chat được render bằng `innerHTML` KHÔNG escape (caro_game.py: chat history khi join, chat realtime, player list) → người chơi đặt tên `<img src=x onerror=...>` hoặc gửi chat chứa `<script>` thì mọi người cùng phòng + người vào sau sẽ thực thi. Sửa: dùng `textContent`/`createTextNode` (hoặc hàm `escapeHtml`) cho MỌI dữ liệu user; server sanitize + giới hạn độ dài tên (~30 ký tự) và message (~200 ký tự).
  - Priority: high | Effort: M
  - Version: v2.5
  - Released: v2.5

- [ ] **Fix (bảo mật): Validate `row`/`col` trong `handle_move`**
  - Mô tả: `row, col = data['row'], data['col']` rồi truy cập `board[row][col]` không kiểm tra kiểu/giới hạn → emit giá trị âm (negative index đưa nước vào ô cuối bàn, bypass logic), hoặc `>= BOARD_SIZE`/string/float → `IndexError`/`TypeError`. Thêm `isinstance(x, int)` + `0 <= x < BOARD_SIZE` trước khi dùng.
  - Priority: medium | Effort: S
  - Version: v2.9

- [ ] **Fix (bảo mật): Giới hạn tạo phòng động + độ dài tên phòng**
  - Mô tả: `handle_join` tạo phòng mới với tên tùy ý không giới hạn → emit `join` hàng nghìn tên phòng random gây DoS bộ nhớ (mỗi phòng kèm board 20x20). Cap số phòng / chỉ cho phép phòng cố định / validate + giới hạn độ dài tên phòng.
  - Priority: medium | Effort: S
  - Version: v2.9

- [ ] **Fix (bảo mật): Rate-limit + giới hạn độ dài chat server-side**
  - Mô tả: `handle_chat` không rate-limit, độ dài chỉ bị giới hạn bởi `maxlength` trên client (dễ bypass) → spam/DoS băng thông. Enforce `len(message) <= 200` ở server + rate-limit đơn giản theo sid.
  - Priority: medium | Effort: S
  - Version: v2.9

- [ ] **Fix: Hiển thị tên người thắng (thắng thường thiếu tên + countdown ghi đè mất tên)**
  - Mô tả: Hai lỗi làm không hiện được tên người thắng: (1) `handle_move` khi thắng thường, payload `game_over` KHÔNG gửi `winner_name` (chỉ gửi `winner` = piece) → frontend chỉ hiện "X ĐÃ CHIẾN THẮNG!" không tên (chỉ riêng đầu hàng mới có `winner_name`); (2) handler `socket.on('countdown')` ghi đè `#info` bằng "Ván mới sau Ns..." → ngay cả khi `game_over` đã set dòng tên người thắng, dòng đó bị thay mất trong lúc đếm ngược. Sửa: backend `handle_move` thêm `winner_name = next((p['name'] for p in r_data['players'].values() if p['piece'] == piece), piece)` vào payload `game_over` (giống `handle_surrender`); frontend tách khu hiển thị kết quả ra một element riêng (vd `#result`) để `countdown` chỉ cập nhật phần "Ván mới sau Ns" chứ không ghi đè tên người thắng; hiển thị "`<tên>` (`<piece>`) THẮNG!" cho cả thắng thường lẫn đầu hàng.
  - Priority: medium | Effort: S
  - Version: v2.9

- [ ] **Fix: Xóa chat_history khi phòng trống hoàn toàn (kể cả đóng tab/tắt trình duyệt)**
  - Mô tả: Đóng tab/tắt trình duyệt CŨNG trigger event `disconnect` của Flask-SocketIO (giống nút "Rời Phòng" vốn chỉ `location.reload()`), nhưng `handle_disconnect` hiện KHÔNG bao giờ xóa `chat_history` — dù người cuối cùng (kể cả khán giả) rời đi, `chat_history` vẫn nằm mãi trong room state (người sau vào phòng thấy hội thoại cũ, rò rỉ bộ nhớ). Bản v2.3 từng có nhánh xóa nhưng SAI điều kiện (xóa khi hết người cầm X/O, bỏ qua khán giả) và sau refactor seat management v2.4, nhánh đó đã bị lược bỏ. Sửa: trong `handle_disconnect`, ngay sau `del r_data['players'][request.sid]`, thêm `if not r_data['players']:` → `r_data['chat_history'] = []` đồng thời reset bàn/ván về trạng thái ban đầu (board rỗng, `turn='X'`, `game_over=False`, `game_active=False`, `last_move`/`win_cells`/`threat_cells` = None/[]). Điều kiện tiền đề: chỉ xóa khi phòng KHÔNG còn ai (kể cả khán giả).
  - Priority: medium | Effort: S
  - Version: v2.9

- [ ] **Fix: 1 IP chỉ được ngồi 1 ghế trên TOÀN bộ phòng (chống spam chỗ bằng nhiều tab/trình duyệt)**
  - Mô tả: Hiện `handle_sit` chỉ kiểm tra trùng IP TRONG CÙNG 1 phòng (vòng `for sid, p in r_data['players'].items()`), nên 1 máy có thể mở nhiều tab/trình duyệt, ngồi 1 ghế ở NHIỀU phòng khác nhau (vd ngồi X cả 3 phòng) → chiếm chỗ, chặn người khác chơi. (Không tự đánh với chính mình được vì mỗi phòng chỉ cho 1 ghế/IP, nhưng vẫn spam chỗ.) Sửa: trong `handle_sit`, ngoài kiểm tra cùng phòng, kiểm tra TOÀN BỘ `rooms` — nếu IP này ĐÃ ngồi (piece X/O) ở bất kỳ phòng NÀO khác → từ chối (khi `ALLOW_SAME_IP=False`).
  - Priority: medium | Effort: S
  - Version: v2.9

- [x] **Feature: Tự động nhả ghế khi người chơi ngồi lì (idle seat timeout)**
  - Mô tả: Người chơi ngồi X/O rồi bỏ đi/quên tắt tab (tab vẫn mở, socket còn sống → KHÔNG trigger `disconnect`) → không đứng dậy cũng không đánh → chiếm ghế vô hạn, chặn người khác chơi. Điển hình: ngồi X, đối thủ ngồi O, mà X không đánh nước đầu → `game_active` mãi `False`, ván không bắt đầu, O chờ vô hạn; hoặc giữa ván tới lượt mà AFK. Giải pháp 2 tầng: (1) **Pre-game idle (làm v2.4.1)** — người ngồi ghi `last_active` (cập nhật khi sit/stand/move/chat/ping); backend định kỳ quét: khi `game_active=False` và người ngồi idle > `IDLE_SECONDS` (mặc định 180s, dễ chỉnh) → tự `stand` (nhả ghế) + notify + broadcast `player_list`/`room_list`; nếu đủ 2 người mà người tới lượt (X) không đánh nước đầu trong hạn → tự đứng người đó, ván về trạng thái chờ. (2) **In-game turn clock (v2.5)** — idle khi tới lượt → **tính thua** (đối thủ thắng ván; đã nằm ở item "Đồng hồ 30s"). Config: `IDLE_SECONDS` (mặc định 180), `TURN_SECONDS`.
  - Priority: medium | Effort: M
  - Version: v2.5
  - Released: v2.5

- [ ] **Fix: Bỏ nút Bật/Tắt cảnh báo (threat toggle)**
  - Mô tả: Tính năng cảnh báo đường nguy hiểm (threat detection) đã hoạt động ổn định → bỏ nút toggle. Xóa nút `#threat-toggle`, hàm `toggleThreat()`, biến `threatEnabled`; trong `updateBoard` bỏ điều kiện `threatEnabled &&` → luôn hiển thị threat cells.
  - Priority: low | Effort: S
  - Version: v2.9

- [ ] **Fix: Seat panel xếp thành 1 hàng ngang (không tràn/đè nút Đầu hàng)**
  - Mô tả: Seat panel hiện là 3 `.seat-row` xếp DỌC (vì `#seat-panel` đang `flex-direction: column` — caro_game.py dòng 64) → Ghế X / Ghế O / nút Đứng lên chiếm 3 dòng, tràn/đè khối `.game-controls` (nút Đầu hàng) bên dưới. Sửa giữ nguyên core (KHÔNG đổi logic JS/handler, chỉ CSS): đổi `#seat-panel` thành `flex-direction: row` + `flex-wrap: wrap; gap: 12px; align-items: center; justify-content: center` để Ghế X + Ghế O + nút Đứng lên nằm trên 1 hàng; có thể gộp `.seat-row` hoặc giữ nguyên từng row thành `inline-flex`. Đảm bảo `#surrender-btn`/`.game-controls` không bị đẩy tràn.
  - Priority: low | Effort: S
  - Version: v2.9

- [ ] **Feature: Tân trang giao diện (UI overhaul) kiểu game online hiện đại — DaisyUI**
  - Mô tả: Giao diện hiện tại (inline CSS, thô) cần trau chuốt. Framework ĐÃ CHỐT: **DaisyUI** (chạy trên Tailwind CSS, load qua CDN, không cần build) — dùng theme + component sẵn (card, badge, button, avatar, chat bubble). Giữ nguyên logic SocketIO/vanilla JS, chỉ làm lại HTML/CSS: lobby = card phòng + badge trạng thái (Trống=`success`/xanh, Đang đợi=`warning`/vàng, Đầy=`error`/đỏ), seat panel = card đẹp, bàn cờ + hiệu ứng, chat box hiện đại. KHÔNG dùng React/Vue/Svelte (quá nặng cho project Flask 1 f-string). Lưu ý: máy LAN không có Internet cần host Tailwind + DaisyUI local.
  - Priority: medium | Effort: L
  - Version: v2.9

- [ ] **Feature: Đồng hồ đếm ngược (30 giây/nước)**
  - Mô tả: Mỗi người chơi có 30 giây cho một nước đi. Hiển thị đồng hồ đếm ngược. Hết giờ sẽ **tính thua** ván đó (đối thủ thắng). Có thể cấu hình thời gian.
  - Priority: medium | Effort: M
  - Version: v2.9

- [ ] **Feature: Bảng xếp hạng người chơi (Leaderboard)**
  - Mô tả: Hiển thị top 5 người chơi theo điểm ELO ở màn hình lobby. Dữ liệu lấy từ `players.json`. Cập nhật real-time sau mỗi ván. Tính cả thắng do disconnect.
  - Priority: medium | Effort: M
  - Version: v2.9

- [ ] **Feature: Hệ số ELO**
  - Mô tả: Tính điểm ELO cho mỗi người chơi, bắt đầu từ 0, thấp nhất là 0 (không âm). Công thức chuẩn: `R' = R + K*(S - E)`, K=32, scale=400. Lưu chung vào `players.json` với key=IP.
  - Priority: medium | Effort: M
  - Version: v2.9

- [ ] **Feature: Tạo phòng động**
  - Mô tả: Cho phép người chơi tạo phòng mới với tên tùy chỉnh, không giới hạn 3 phòng cố định. Có danh sách phòng đang hoạt động. **Kèm dọn phòng động khi trống sau X phút** (xoá khỏi `rooms` để tránh rò rỉ bộ nhớ). (Gộp từ item "Tự động dọn phòng trống" cũ — 3 phòng cố định hiện đã tự reset khi hết người nên không cần mục riêng.)
  - Priority: low | Effort: L


## Archive (đã release)

---

# Pet Game (Nuôi Thú Ảo)

## Version 1.0 (chuẩn bị release đầu tiên)

- [ ] **Core: Tamagotchi cổ điển + casual (hạn chế cày cuốc)**
  - Mô tả: 4 chỉ số (Hunger, Happiness, Energy, Health) 0-100. Tốc độ giảm chậm: Hunger -1/10ph, Happiness -1/15ph, Energy -1/20ph (config). Health là chỉ số dẫn xuất (giảm khi chỉ số khác = 0, hồi khi đủ ăn/vui/khỏe). 6 hành động: Feed, Play, Sleep, Heal, Clean, Release. **Không có "thú bỏ đi"** — Health=0 → "ốm nặng", thú không bao giờ mất. Single screen, progress bar + thú giữa + nút hành động.
  - Priority: high | Effort: L
  - Version: Pet v1.0

- [ ] **Core: Lưu trữ timestamp catch-up**
  - Mô tả: Lưu `pets.json` key=IP. Mỗi thú lưu `last_updated` (epoch), các chỉ số, `age_hours`, `in_center`. Dùng timestamp catch-up (không dùng vòng lặp tick) để tính bù đúng khi server tắt qua đêm/cuối tuần. Server Flask chạy giờ hành chính.
  - Priority: high | Effort: M
  - Version: Pet v1.0

- [ ] **Feature: Chọn Pokémon ngẫu nhiên (spin)**
  - Mô tả: Nút "🎲 Quay" hiển thị 3 Pokémon ngẫu nhiên cho lựa chọn, bấm lại nhiều lần. Chỉ hiện Pokémon base form (dạng đầu tiên của chuỗi tiến hóa), ~127 con từ Gen 1-2. Dùng cấu trúc `EVOLUTION_TREE` (map ID → list nhánh kế tiếp) để xác định base form.
  - Priority: high | Effort: M
  - Version: Pet v1.0

- [ ] **Feature: Pokémon huyền thoại & bí ẩn — 1 con duy nhất/toàn server**
  - Mô tả: Phân nhóm hiếm: `LEGENDARY_IDS = {144,145,146,150,243,244,245,249,250}` (9 Huyền thoại) và `MYTHICAL_IDS = {151,251}` (2 Bí ẩn: Mew, Celebi). Registry toàn cục `legendary.json` (`species_id → ip`) — mỗi loài **chỉ tồn tại đúng 1 con trên toàn server**; loài đã có chủ bị loại khỏi pool roll. Claim khi bấm nhận con (adopt), không phải lúc hiện 3 ô quay; nếu bị người khác claim trước → thông báo "đã có chủ". Release (Thả) → trả slot về pool. Xác suất roll 3 tầng cho mỗi ô quay: (1) `LEGENDARY_CHANCE = 0.001` (0.1%) trúng *tầng hiếm*; (2) nếu trúng → sub-roll `MYTHICAL_CHANCE = 0.1` (10%) rơi nhóm Bí ẩn, còn lại (90%) là Huyền thoại; (3) chọn ngẫu nhiên đều trong các loài chưa có chủ của nhóm tương ứng. Fallback: nhóm trúng đã cạn → rơi nhóm hiếm còn lại; cả hai cạn → Pokémon thường. Xác suất tuyệt đối: Huyền thoại ≈ 0.09%, Bí ẩn ≈ 0.01% (1/10.000) mỗi ô.
  - Priority: high | Effort: M
  - Version: Pet v1.0

- [ ] **Feature: Tiến hóa (đa nhánh + hiệu ứng hoành tráng)**
  - Mô tả: Tiến hóa tự động theo tuổi (`age_hours` mốc 24h/72h). Đa nhánh → người chơi chọn nhánh khi tiến hóa (modal hiển thị các lựa chọn, vd Eevee→5 nhánh, Poliwhirl→2 nhánh). **Hiệu ứng tiến hóa hoành tráng** là tính năng signature: màn hình tối dần, sáng lấp lánh ⭐, âm thanh, silhouette thú biến đổi, thông báo "X đang tiến hóa thành Y!".
  - Priority: high | Effort: L
  - Version: Pet v1.1

- [ ] **Feature: Nút Thả Pokémon**
  - Mô tả: Nút "Thả Pokémon" (có confirm modal). Thả thú hiện tại → quay lại màn hình chọn Pokémon (spin). Mất tiến trình cũ.
  - Priority: medium | Effort: S
  - Version: Pet v1.0

- [ ] **Feature: Gửi vào Trung tâm Pokémon (Pokemon Center)**
  - Mô tả: Miễn phí, không cooldown, vô hạn thời gian. Khi ở Trung tâm: đóng băng toàn bộ (4 chỉ số + tuổi không đổi, không heal). UI inline: Poké Ball 🏥, thanh chỉ số xám giữ nguyên, vô hiệu 6 nút, hiện nút "📥 Nhận thú về". Hiển thị "Đã gửi X giờ/ngày".
  - Priority: high | Effort: M
  - Version: Pet v1.0

- [ ] **Feature: Hiển thị Pokémon (Home PNG)**
  - Mô tả: Dùng sprite Home PNG 256x256 Gen 1-2 (đã download 251 sprites vào `pet-game/static/sprites/`). Thú phản ứng theo trạng thái (ốm → xám/băng bó, ngủ → ZZz, ăn → nhai).
  - Priority: high | Effort: M
  - Version: Pet v1.0

- [ ] **Tích hợp: Mount vào Hub**
  - Mô tả: Mount pet_game vào hub.py dưới route `/pet`. Chung SocketIO instance với Caro.
  - Priority: medium | Effort: M
  - Version: Pet v1.0 (phụ thuộc Hub)

---

# Team

- [x] **Tuyển BA Game Agent (ba-game)**
  - Mô tả: Tạo agent BA chuyên về game để phân tích yêu cầu người chơi, dịch thành spec kỹ thuật.
  - Priority: high | Effort: S
  - Released: v2.1 (team)

- [x] **Tuyển Security Agent (security)**
  - Mô tả: Tạo agent `.opencode/agents/security.md` (mode `subagent`, `edit: deny`) chuyên rà soát lỗ hổng bảo mật toàn hệ thống: Flask routes, SocketIO handlers, định danh IP, file storage, XSS/CSRF/injection, secrets, DoS, config sai. Quy trình mới: TRƯỚC mỗi release, PM giao Security review → chỉ release khi không còn lỗ hổng Critical/High (hoặc đã có kế hoạch xử lý).
  - Priority: high | Effort: S
  - Released: v2.4.1 (team)