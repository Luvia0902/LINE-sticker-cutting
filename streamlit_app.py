import streamlit as st
from PIL import Image, ImageDraw
import io
import zipfile
import os

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

# ==========================================
# 常數設定 (與 GUI 版本保持一致)
# ==========================================
STICKER_SIZE = (370, 320)       # LINE 官方貼圖尺寸
MAIN_IMAGE_SIZE = (240, 240)    # 主要圖片（商店展示用）
TAB_IMAGE_SIZE = (96, 74)       # 聊天室標籤圖片
STICKER_PADDING = 10            # 貼圖預設留白（px）

# 預設貼圖集規格
SHEET_WIDTH_DEFAULT = 2560
SHEET_HEIGHT_DEFAULT = 1664
SHEET_ROWS_DEFAULT = 4
SHEET_COLS_DEFAULT = 5

# ==========================================
# 核心邏輯函式
# ==========================================

def add_padding_to_image(img, padding):
    """為圖片添加透明留白邊距"""
    new_width = img.width - (padding * 2)
    new_height = img.height - (padding * 2)
    
    if new_width <= 0 or new_height <= 0:
        return img
    
    img_shrunk = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    result = Image.new('RGBA', (img.width, img.height), (255, 255, 255, 0))
    
    offset = ((img.width - new_width) // 2, (img.height - new_height) // 2)
    result.paste(img_shrunk, offset, img_shrunk if img_shrunk.mode == 'RGBA' else None)
    return result

def create_main_image(sticker_img):
    """創建主要圖片 240x240"""
    main_img = sticker_img.resize(MAIN_IMAGE_SIZE, Image.Resampling.LANCZOS)
    if main_img.mode != 'RGBA':
        main_img = main_img.convert('RGBA')
    return main_img

def create_tab_image(sticker_img):
    """創建標籤圖片 96x74"""
    tab_img = sticker_img.resize(TAB_IMAGE_SIZE, Image.Resampling.LANCZOS)
    if tab_img.mode != 'RGBA':
        tab_img = tab_img.convert('RGBA')
    return tab_img

def process_image(image_file, rows, cols, scale_percent, add_padding, fit_mode, gen_main, gen_tab, offset_x=0, offset_y=0, fixed_size_mode=False, do_remove_bg=False):
    """
    處理圖片切割邏輯
    returns: bytes_io of zip file, info_text
    """
    img = Image.open(image_file)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # 準備 Zip 檔
    zip_buffer = io.BytesIO()
    
    count = 0
    stickers_for_extras = []
    
    if fixed_size_mode:
        cell_w, cell_h = 512, 416 # 2560/5, 1664/4
    else:
        cell_w = img.width / cols
        cell_h = img.height / rows
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for row in range(rows):
            for col in range(cols):
                count += 1
                
                # 計算裁切區域 (加入偏移量)
                left = int(col * cell_w + offset_x)
                top = int(row * cell_h + offset_y)
                
                if fixed_size_mode:
                    right = left + 512
                    bottom = top + 416
                else:
                    right = int((col + 1) * cell_w + offset_x)
                    bottom = int((row + 1) * cell_h + offset_y)
                
                # 邊界保護
                if left < 0: left = 0
                if top < 0: top = 0
                if right > img.width: right = img.width
                if bottom > img.height: bottom = img.height
                
                if right <= left or bottom <= top:
                    # 無效區域跳過
                    continue

                sticker = img.crop((left, top, right, bottom))
                
                # 去背處理
                if do_remove_bg and REMBG_AVAILABLE:
                    sticker = remove(sticker)

                # 添加留白
                if add_padding:
                    sticker_processed = add_padding_to_image(sticker, STICKER_PADDING)
                else:
                    sticker_processed = sticker
                
                # 縮放處理 (輸出固定為 370x320)
                # ... 剩餘邏輯保持不變 ...
                
                # 縮放處理 (輸出固定為 370x320)
                target_w, target_h = sticker_processed.size
                
                # 計算內容縮放
                content_w = int(target_w * scale_percent / 100)
                content_h = int(target_h * scale_percent / 100)
                if content_w <= 0: content_w = 1
                if content_h <= 0: content_h = 1
                
                content_scaled = sticker_processed.resize((content_w, content_h), Image.Resampling.LANCZOS)
                
                # 建立最終畫布
                sticker_final = Image.new('RGBA', STICKER_SIZE, (255, 255, 255, 0))
                
                # 適應模式 or 一般置中
                if fit_mode and (content_w > STICKER_SIZE[0] or content_h > STICKER_SIZE[1]):
                    # 縮小以適應
                    ratio = min(STICKER_SIZE[0] / content_w, STICKER_SIZE[1] / content_h)
                    fitted_w = int(content_w * ratio)
                    fitted_h = int(content_h * ratio)
                    content_fitted = content_scaled.resize((fitted_w, fitted_h), Image.Resampling.LANCZOS)
                    
                    paste_x = (STICKER_SIZE[0] - fitted_w) // 2
                    paste_y = (STICKER_SIZE[1] - fitted_h) // 2
                    sticker_final.paste(content_fitted, (paste_x, paste_y), content_fitted)
                else:
                    # 直接置中
                    paste_x = (STICKER_SIZE[0] - content_w) // 2
                    paste_y = (STICKER_SIZE[1] - content_h) // 2
                    sticker_final.paste(content_scaled, (paste_x, paste_y), content_scaled)
                
                # 存入 Zip
                img_byte_arr = io.BytesIO()
                sticker_final.save(img_byte_arr, format='PNG')
                zf.writestr(f"sticker_{count:02d}.png", img_byte_arr.getvalue())
                
                if count == 1:
                    stickers_for_extras.append(sticker_final.copy())

        # 生成額外圖片
        if gen_main and stickers_for_extras:
            main_img = create_main_image(stickers_for_extras[0])
            img_byte_arr = io.BytesIO()
            main_img.save(img_byte_arr, format='PNG')
            zf.writestr("main.png", img_byte_arr.getvalue())
            
        if gen_tab and stickers_for_extras:
            tab_img = create_tab_image(stickers_for_extras[0])
            img_byte_arr = io.BytesIO()
            tab_img.save(img_byte_arr, format='PNG')
            zf.writestr("tab.png", img_byte_arr.getvalue())

    zip_buffer.seek(0)
    return zip_buffer, count

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="LINE 貼圖切割神器", page_icon="✂️", layout="wide")

st.title("✂️ LINE 貼圖切割神器 (線上版)")
st.markdown("""
這是一個簡單的線上工具，幫您將做好的「整張貼圖集」切割成符合 LINE 官方規格的獨立貼圖檔案。
- **輸入**：一張包含多個貼圖的大圖 (例如 2560x1664)
- **輸出**：自動切割、縮放並依序命名的 ZIP 壓縮包
""")

# Sidebar 設定
st.sidebar.header("⚙️ 設定參數")

# 規格預設
st.sidebar.subheader("📐 切割佈局")
use_default = st.sidebar.checkbox("使用標準規格 (4x5, 20張)", value=True)
fixed_size_mode = st.sidebar.checkbox("🔒 固定尺寸模式 (512x416)", value=False, help="忽略圖片大小，使用固定間距進行裁切")

if use_default:
    rows = 4
    cols = 5
else:
    cols = st.sidebar.number_input("垂直切割 (欄)", min_value=1, value=5)
    rows = st.sidebar.number_input("水平切割 (列)", min_value=1, value=4)

st.sidebar.divider()

# 手動微調
st.sidebar.subheader("🎯 網格微調")
offset_x = st.sidebar.slider("水平位移 (X)", -500, 500, 0, help="整體網格向左/右平移")
offset_y = st.sidebar.slider("垂直位移 (Y)", -500, 500, 0, help="整體網格向上/下平移")

st.sidebar.divider()

# 輸出設定
st.sidebar.subheader("🎨 輸出微調")
add_padding = st.sidebar.checkbox("添加邊距留白 (10px)", value=True, help="在貼圖周圍保留透明邊距，避免貼圖看起來太擁擠")
scale_percent = st.sidebar.slider("內容縮放比例 (%)", 50, 150, 100, help="調整貼圖內容的大小")
fit_mode = st.sidebar.checkbox("智能適應模式", value=True, help="如果圖片縮放後超出邊界，自動縮小以完整顯示")

# 去背功能
st.sidebar.divider()
st.sidebar.subheader("🧹 進階處理")
if REMBG_AVAILABLE:
    do_remove_bg = st.sidebar.checkbox("自動去除背景 (AI)", value=False, help="使用 AI 模型自動移除背景（首次執行較慢）")
else:
    st.sidebar.info("💡 如需去背功能，請安裝 `rembg` 與 `onnxruntime` 套件。")
    do_remove_bg = False

# 額外檔案
st.sidebar.divider()
st.sidebar.subheader("📦 額外生成")
gen_main = st.sidebar.checkbox("生成主要圖片 (main.png)", value=True)
gen_tab = st.sidebar.checkbox("生成標籤圖片 (tab.png)", value=True)

# 主要區域
upload_file = st.file_uploader("請上傳要切割的圖片 (PNG/JPG)", type=['png', 'jpg', 'jpeg'])

if upload_file:
    image = Image.open(upload_file)
    st.info(f"圖片載入成功！原始尺寸：{image.width} x {image.height} px")

    # 預覽區域
    st.subheader("👀 切割預覽")
    
    # 繪製網格預覽
    preview_img = image.copy().convert("RGBA")
    draw = ImageDraw.Draw(preview_img)
    
    if fixed_size_mode:
        cell_w, cell_h = 512, 416
    else:
        cell_w = image.width / cols
        cell_h = image.height / rows
    
    # 畫垂直線
    for i in range(cols + 1):
        x = int(i * cell_w + offset_x)
        if 0 <= x <= image.width:
            draw.line([(x, 0), (x, image.height)], fill="red", width=5)
        
    # 畫水平線
    for i in range(rows + 1):
        y = int(i * cell_h + offset_y)
        if 0 <= y <= image.height:
            draw.line([(0, y), (image.width, y)], fill="red", width=5)
        
    # 顯示預覽 (縮小一點以免太大)
    st.image(preview_img, caption=f"預覽切割網格 ({rows}列 x {cols}欄)", use_container_width=True)
    
    # 執行按鈕
    col1, col2 = st.columns([1, 2])
    with col1:
        process_btn = st.button("🚀 開始切割並下載", type="primary", use_container_width=True)
    
    if process_btn:
        with st.spinner("正在處理圖片..."):
            try:
                zip_data, count = process_image(
                    upload_file, rows, cols, scale_percent, 
                    add_padding, fit_mode, gen_main, gen_tab,
                    offset_x=offset_x, offset_y=offset_y,
                    fixed_size_mode=fixed_size_mode,
                    do_remove_bg=do_remove_bg
                )
                
                st.success(f"成功切割 {count} 張貼圖！")
                
                # 下載按鈕
                st.download_button(
                    label="📥 下載 ZIP 壓縮包",
                    data=zip_data,
                    file_name="line_stickers.zip",
                    mime="application/zip",
                    type="primary"
                )
                
            except Exception as e:
                st.error(f"發生錯誤：{str(e)}")
else:
    st.warning("👈 請先從左側選單確認設定，並上傳圖片")

