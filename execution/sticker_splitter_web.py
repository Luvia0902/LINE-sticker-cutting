
import streamlit as st
from PIL import Image, ImageDraw
import io
import zipfile
import time
from pathlib import Path

# --- Constants (Same as GUI) ---
STICKER_SIZE = (370, 320)
MAIN_IMAGE_SIZE = (240, 240)
TAB_IMAGE_SIZE = (96, 74)
STICKER_PADDING = 10
SHEET_WIDTH = 2560
SHEET_HEIGHT = 1664
SHEET_ROWS = 4
SHEET_COLS = 5

# --- Helper Functions ---

def add_padding_to_image(img, padding):
    """為圖片添加留白邊距"""
    new_width = img.width - (padding * 2)
    new_height = img.height - (padding * 2)
    
    if new_width <= 0 or new_height <= 0:
        return img
    
    # 縮小原圖以留出邊距
    img_shrunk = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 創建透明背景
    result = Image.new('RGBA', (img.width, img.height), (255, 255, 255, 0))
    
    # 將縮小的圖片貼到中央
    offset = ((img.width - new_width) // 2, (img.height - new_height) // 2)
    result.paste(img_shrunk, offset, img_shrunk if img_shrunk.mode == 'RGBA' else None)
    
    return result

def create_main_image(sticker_img):
    """創建主要圖片 (240x240)"""
    main_img = sticker_img.resize(MAIN_IMAGE_SIZE, Image.Resampling.LANCZOS)
    if main_img.mode != 'RGBA':
        main_img = main_img.convert('RGBA')
    return main_img

def create_tab_image(sticker_img):
    """創建標籤圖片 (96x74)"""
    tab_img = sticker_img.resize(TAB_IMAGE_SIZE, Image.Resampling.LANCZOS)
    if tab_img.mode != 'RGBA':
        tab_img = tab_img.convert('RGBA')
    return tab_img

def get_sorted_markers(total_size, count, offsets, fixed_size_mode=False):
    """計算並返回排序後的網格切割線位置"""
    markers = []
    
    # 判斷是垂直(X)還是水平(Y) - 這裡稍微簡化，因為沒有類別上下文
    # offsets 應該是 dict {index: value}
    
    if fixed_size_mode:
        # 這裡需要傳入 axis 資訊比較好，但我們可以透過 total_size 猜測或傳參數
        # 簡化：假設外部確實傳入了正確的單元大小依賴
        # 暫時用 total_size / count 作為 fallback，但我們會傳入 True/False
        # 為了準確，我們修改函式簽名或邏輯
        # 這裡使用簡單邏輯：
        cell_size = total_size / max(count, 1) # Fallback
    else:
        cell_size = total_size / max(count, 1)
        
    for i in range(count + 1):
        base_pos = i * cell_size
        offset = offsets.get(i, 0)
        markers.append(int(base_pos + offset))
        
    markers.sort()
    return markers

def draw_grid_on_image(image, rows, cols, offset_x, offset_y, v_offsets, h_offsets, fixed_size_mode=False):
    """在圖片上繪製預覽網格"""
    preview_img = image.copy()
    draw = ImageDraw.Draw(preview_img)
    
    width, height = image.size
    
    # 計算單元格大小 (僅用於非固定模式的基礎計算)
    cell_w = width / max(cols, 1)
    cell_h = height / max(rows, 1)
    
    # 如果是固定模式，基礎計算應基於 370x320? 
    # 原 GUI 邏輯：fixed_mode 下 base_unit = STICKER_SIZE
    # 這裡我們需要重現 GUI 的邏輯
    
    # 垂直線 (Vertical lines)
    col_markers = []
    for i in range(cols + 1):
        if fixed_size_mode:
            base_pos = i * STICKER_SIZE[0]
        else:
            base_pos = i * cell_w
            
        pos = int(base_pos + v_offsets.get(i, 0) + offset_x)
        col_markers.append(pos)
        
        # Draw Line
        draw.line([(pos, 0), (pos, height)], fill="red", width=2)
        
    # 水平線 (Horizontal lines)
    row_markers = []
    for i in range(rows + 1):
        if fixed_size_mode:
            base_pos = i * STICKER_SIZE[1]
        else:
            base_pos = i * cell_h
            
        pos = int(base_pos + h_offsets.get(i, 0) + offset_y)
        row_markers.append(pos)
        
        # Draw Line
        draw.line([(0, pos), (width, pos)], fill="red", width=2)
        
    return preview_img, col_markers, row_markers

# --- Main App ---

def main():
    st.set_page_config(page_title="LINE 貼圖切割工具", page_icon="✂️", layout="wide")
    
    st.title("🎨 LINE 貼圖切割工具 (Web版)")
    st.markdown("""
    這個工具可以協助您將設計好的貼圖大海報切割成 LINE 官方規格的貼圖檔案。
    - 支援自定義切割線
    - 自動生成 Main/Tab 圖片
    - 支援即時預覽
    """)
    
    # --- Sidebar Settings ---
    st.sidebar.header("⚙️ 設定")
    
    # Input
    uploaded_file = st.sidebar.file_uploader("上傳圖片", type=['png', 'jpg', 'jpeg'])
    
    # Specs
    use_line_spec = st.sidebar.checkbox("使用標準貼圖集規格 (4x5)", value=False)
    
    if use_line_spec:
        rows = st.sidebar.number_input("列數 (Rows)", value=SHEET_ROWS, disabled=True)
        cols = st.sidebar.number_input("欄數 (Cols)", value=SHEET_COLS, disabled=True)
        fixed_size_mode = False # 標準規格通常也是鋪滿
    else:
        c1, c2 = st.sidebar.columns(2)
        rows = c1.number_input("列數 (Rows)", min_value=1, value=1)
        cols = c2.number_input("欄數 (Cols)", min_value=1, value=1)
        fixed_size_mode = st.sidebar.checkbox("使用固定裁切尺寸 (370x320)", value=False)

    # Global Offsets
    st.sidebar.subheader("整體偏移")
    c3, c4 = st.sidebar.columns(2)
    offset_x = c3.number_input("X 軸偏移", value=0)
    offset_y = c4.number_input("Y 軸偏移", value=0)
    
    # Spec Details
    st.sidebar.subheader("輸出選項")
    add_padding = st.sidebar.checkbox("添加留白邊距 (10px)", value=True)
    gen_main = st.sidebar.checkbox("生成主要圖片 (Main)", value=True)
    gen_tab = st.sidebar.checkbox("生成標籤圖片 (Tab)", value=True)
    fit_mode = st.sidebar.checkbox("智能縮放適應 (Fit)", value=True)
    scale_percent = st.sidebar.slider("縮放百分比", 50, 150, 100)
    
    # Advanced: Manual Grid adjustments (simplified for Web)
    st.sidebar.markdown("---")
    st.sidebar.subheader("進階：個別線條微調")
    with st.sidebar.expander("展開微調選項"):
        v_offsets = {}
        h_offsets = {}
        
        st.caption("垂直線偏移 (Vertical)")
        for i in range(cols + 1):
            v_offsets[i] = st.number_input(f"V-Line {i}", value=0, key=f"v_{i}")
            
        st.caption("水平線偏移 (Horizontal)")
        for i in range(rows + 1):
            h_offsets[i] = st.number_input(f"H-Line {i}", value=0, key=f"h_{i}")

    # --- Main Area ---
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        
        # Preview
        st.subheader("預覽與切割線")
        
        # Calculate and Draw Grid on Image
        preview_img, col_markers, row_markers = draw_grid_on_image(
            image, rows, cols, offset_x, offset_y, v_offsets, h_offsets, fixed_size_mode
        )
        
        st.image(preview_img, caption=f"原始尺寸: {image.width}x{image.height}", use_column_width=True)
        
        # Markers info
        if st.checkbox("顯示切割座標詳細資訊"):
            st.write("垂直切割線 (X):", col_markers)
            st.write("水平切割線 (Y):", row_markers)
            
        # Process Button
        if st.button("🚀 開始切割並下載", type="primary"):
            with st.spinner("正在處理圖片..."):
                # --- Processing Logic ---
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    count = 0
                    stickers_for_extras = []
                    
                    # 排序並處理 markers (draw 已經算過了，但那是為了畫圖，這裡為了保險重算一次邏輯確保一致)
                    # 注意：draw_grid_on_image 回傳的 col_markers 是已經加了 offset_x 且排序好的嗎?
                    # 上面的實作只是 append 然後傳回，沒有 sort。且包含了 offset。
                    # 為了穩健，我們這裡重寫邏輯
                    
                    # 1. 準備基礎 markers
                    final_col_markers = []
                    if fixed_size_mode:
                        base_unit_w = STICKER_SIZE[0]
                    else:
                        base_unit_w = image.width / max(cols, 1)
                        
                    for i in range(cols + 1):
                        base = i * base_unit_w
                        off = v_offsets.get(i, 0)
                        final_col_markers.append(int(base + off)) # 尚未加 global x
                    final_col_markers.sort()
                    
                    final_row_markers = []
                    if fixed_size_mode:
                        base_unit_h = STICKER_SIZE[1]
                    else:
                        base_unit_h = image.height / max(rows, 1)
                        
                    for i in range(rows + 1):
                        base = i * base_unit_h
                        off = h_offsets.get(i, 0)
                        final_row_markers.append(int(base + off))
                    final_row_markers.sort()

                    # Loop through grid
                    for r in range(rows):
                        for c in range(cols):
                            count += 1
                            
                            # Check bounds
                            if r >= len(final_row_markers) - 1 or c >= len(final_col_markers) - 1:
                                continue
                                
                            # Calculate Crop Box
                            # Add global offsets here
                            left = final_col_markers[c] + offset_x
                            top = final_row_markers[r] + offset_y
                            right = final_col_markers[c+1] + offset_x
                            bottom = final_row_markers[r+1] + offset_y
                            
                            if right <= left: right = left + 1
                            if bottom <= top: bottom = top + 1
                            
                            # Crop
                            try:
                                sticker = image.crop((int(left), int(top), int(right), int(bottom)))
                            except Exception:
                                sticker = Image.new('RGBA', STICKER_SIZE, (255, 255, 255, 0))
                                
                            # Padding
                            if add_padding:
                                sticker = add_padding_to_image(sticker, STICKER_PADDING)
                                
                            # Scaling & Resizing logic
                            target_w, target_h = STICKER_SIZE
                            
                            is_scaling = (scale_percent != 100 or fixed_size_mode or True)
                            
                            if is_scaling:
                                if fixed_size_mode:
                                     # Fixed: base on 370x320
                                     tw, th = STICKER_SIZE
                                else:
                                     # Normal: base on actual crop
                                     tw, th = sticker.width, sticker.height
                                     
                                content_w = int(tw * scale_percent / 100)
                                content_h = int(th * scale_percent / 100)
                                if content_w <=0: content_w=1
                                if content_h <=0: content_h=1
                                
                                content_scaled = sticker.resize((content_w, content_h), Image.Resampling.LANCZOS)
                                
                                # Paste onto 370x320 canvas
                                final_sticker = Image.new('RGBA', STICKER_SIZE, (255, 255, 255, 0))
                                
                                if fit_mode and (content_w > STICKER_SIZE[0] or content_h > STICKER_SIZE[1]):
                                    ratio = min(STICKER_SIZE[0]/content_w, STICKER_SIZE[1]/content_h)
                                    fw = int(content_w * ratio)
                                    fh = int(content_h * ratio)
                                    content_fitted = content_scaled.resize((fw, fh), Image.Resampling.LANCZOS)
                                    px = (STICKER_SIZE[0] - fw) // 2
                                    py = (STICKER_SIZE[1] - fh) // 2
                                    final_sticker.paste(content_fitted, (px, py), content_fitted if content_fitted.mode=='RGBA' else None)
                                else:
                                    px = (STICKER_SIZE[0] - content_w) // 2
                                    py = (STICKER_SIZE[1] - content_h) // 2
                                    final_sticker.paste(content_scaled, (px, py), content_scaled if content_scaled.mode=='RGBA' else None)
                            else:
                                final_sticker = sticker.resize(STICKER_SIZE, Image.Resampling.LANCZOS)
                                
                            # Save to ZIP
                            img_byte_arr = io.BytesIO()
                            final_sticker.save(img_byte_arr, format='PNG')
                            zip_file.writestr(f"sticker_{count:02d}.png", img_byte_arr.getvalue())
                            
                            if count == 1:
                                stickers_for_extras.append(final_sticker.copy())
                                
                    # Extras
                    if gen_main and stickers_for_extras:
                        main_img = create_main_image(stickers_for_extras[0])
                        img_byte_arr = io.BytesIO()
                        main_img.save(img_byte_arr, format='PNG')
                        zip_file.writestr("main.png", img_byte_arr.getvalue())
                        
                    if gen_tab and stickers_for_extras:
                        tab_img = create_tab_image(stickers_for_extras[0])
                        img_byte_arr = io.BytesIO()
                        tab_img.save(img_byte_arr, format='PNG')
                        zip_file.writestr("tab.png", img_byte_arr.getvalue())
                        
                st.success(f"處理完成！共 {count} 張貼圖。")
                
                # Download Button
                st.download_button(
                    label="📥 下載貼圖包 (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="stickers.zip",
                    mime="application/zip"
                )

    else:
        st.info("請從左側上傳圖片以開始。")

if __name__ == "__main__":
    main()
