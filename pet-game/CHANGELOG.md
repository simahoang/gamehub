# Changelog - Pet Game

## v1.1 (2026-08-22)

### Refactor
- **SQLite Migration**: Thay thế JSON file storage (`pets.json`, `legendary.json`) bằng SQLite database với WAL mode. Fix bug CRITICAL mất dữ liệu khi server chạy qua đêm. Tự động migrate dữ liệu cũ từ JSON.

### Bảo mật
- **Server-side Spin State**: Chặn F12/script claim Pokémon tuỳ ý. Server lưu spin state (3 species_id) theo IP, verify khi adopt. TTL 120s.
- **Rate-limit Spin**: Giới hạn 1 lần quay / 2 giây / IP, chống auto-spin script.
- **Cooldown 60s**: Mỗi hành động (Feed/Play/Sleep/Heal) có 60s hồi chiêu, chống spam max chỉ số.
- **Atomic transaction**: Gộp SELECT + UPDATE vào cùng transaction cho center/receive/release, tránh race condition.
- **SECRET_KEY**: Thay hardcode bằng `secrets.token_hex(32)` fallback (hub.py).

### Tính năng mới
- **Hiển thị loại Pokémon**: Badge ⭐ Huyền thoại / ✨ Bí ẩn hiển thị trên màn hình chính bên cạnh tên Pokémon.
- **Hệ thống vệ sinh**: Thú tự đi vệ sinh (💩) theo chu kỳ 2-4h. Phân gây giảm Happiness. Nút Clean dọn từng cục + hồi Happiness.
- **Hiệu ứng Play**: Sprite bounce animation + emoji 🎾 khi bấm Chơi.

### Tinh chỉnh
- **Ẩn chỉ số Sức khỏe (Health)**: Tạm ẩn Health bar + nút Chữa, để dành cho tính năng Chiến đấu sau này.

---

## v1.0 (2026-08-19)

### Tính năng ban đầu
- UI DaisyUI thống nhất với Caro
- Tamagotchi cổ điển: 4 chỉ số (Hunger, Happiness, Energy, Health)
- Chọn Pokémon ngẫu nhiên (spin 3 con, Gen 1-2)
- Pokémon huyền thoại & bí ẩn (1 con duy nhất/toàn server)
- Nút Thả Pokémon, Gửi vào Trung tâm Pokémon
- Hiển thị sprite Home PNG 256x256
- Mount vào Hub dưới route `/pet`