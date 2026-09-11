# NC-Render AI Studio v1.0.3 — CÀI ĐẶT

## Cách cài nhanh nhất (KHÔNG cần .mzp)

### Bước 1: Copy MacroScript vào 3ds Max

```
Copy tất cả file .mcr trong folder usermacros/ vào:
C:\Users\HOMIE\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\usermacros\
```

Các file cần copy:
- `usermacros/NC_Render_Bridge_v1.mcr` ← MacroScript chính
- `usermacros/NC_Render_Bridge.mcr` ← MacroScript phụ (nếu có)

### Bước 2: Restart 3ds Max

Đóng hoàn toàn 3ds Max (kể cả tray icon), mở lại.

### Bước 3: Kiểm tra

Vào `Customize → Customize User Interface` → tab `MacroScripts` → tìm `NC-Render` hoặc `NCRenderSmartBridge`.

Nếu thấy → plugin hoạt động. Vào dialog để test render.

---

## Cách cài qua .mzp (NẾU HỖ TRỢ)

Nếu 3ds Max 2024 của bạn hỗ trợ cài MZP qua Extension Manager:

1. `Customize → Configure → Extensions → Install`
2. Chọn file `NC_Render_Standard_v1.mzp`
3. Chờ dialog cài đặt hiện ra

**Nếu kéo file .mzp vào 3ds Max mà không có gì xảy ra** → dùng cách cài thủ công bên trên.

---

## Cấu trúc sau cài đặt

```
C:\Users\HOMIE\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\usermacros\
├── NC_Render_Bridge_v1.mcr    ← MacroScript chính (có pythonBin path)
└── NC_Render_Bridge.mcr       ← MacroScript phụ

Plugin folder (giữ nguyên):
D:\Program\setup 3dsmax\Plugins\NC_Render_Standard\
├── mzp.run                    ← Script cài đặt (đọc khi kéo .mzp)
├── scripts\                   ← Python scripts (cuda_render_tool.py, sd_generate.py...)
├── skill\                     ← CUDA Render Skill
└── usericons\                 ← Icons
```

## Yêu cầu hệ thống

- 3ds Max 2024 (64-bit)
- Python 3.11+ với PyTorch CUDA 12.8
- NVIDIA GPU với CUDA support (tested: RTX 3050 8GB)

## Xử lý lỗi

Nếu macroScript không xuất hiện sau khi restart:
1. Mở MaxScript Listener (F11)
2. Gõ: `macroScripts` → xem có `NC_Render_Bridge` không
3. Nếu không có: `file > Open` → mở `NC_Render_Bridge_v1.mcr` → Run
