#!/usr/bin/env python3
"""
Script Name: sticker_splitter_gui.py
Purpose: LINE 貼圖切割工具 - GUI 版本
Author: Agent System
Created: 2026-01-11

支援精確的貼圖集切割規格：
- 整體畫幅：2560 × 1664 px
- 佈局：4 橫排 × 5 直欄 = 20 張貼圖
- 每張貼圖：512 × 416 px（自動計算）
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk
import threading

# LINE 貼圖官方規格
STICKER_SIZE = (370, 320)  # LINE 官方尺寸
MAIN_IMAGE_SIZE = (240, 240)  # 主要圖片（商店展示用）
TAB_IMAGE_SIZE = (96, 74)  # 聊天室標籤圖片
STICKER_PADDING = 10  # 貼圖留白（px）
MAX_FILE_SIZE_MB = 1  # 最大檔案大小 1MB

# 貼圖集標準規格
SHEET_WIDTH = 2560
SHEET_HEIGHT = 1664
SHEET_ROWS = 4
SHEET_COLS = 5
CELL_WIDTH = SHEET_WIDTH // SHEET_COLS  # 512 px
CELL_HEIGHT = SHEET_HEIGHT // SHEET_ROWS  # 416 px

class StickerSplitterGUI:
    """LINE 貼圖切割工具 GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("LINE 貼圖切割工具 v1.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 變數
        self.input_path = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(Path('.tmp/output/stickers').absolute()))
        self.rows = tk.IntVar(value=1)  # 預設 1 (無切割)
        self.cols = tk.IntVar(value=1)  # 預設 1 (無切割)
        self.sheet_width = tk.IntVar(value=SHEET_WIDTH)
        self.sheet_height = tk.IntVar(value=SHEET_HEIGHT)
        self.use_line_spec = tk.BooleanVar(value=False)  # 預設不使用標準規格
        self.add_padding = tk.BooleanVar(value=True)  # 添加留白
        self.generate_main_image = tk.BooleanVar(value=True)  # 生成主要圖片
        self.generate_tab_image = tk.BooleanVar(value=True)  # 生成標籤圖片
        self.main_sticker_index = tk.IntVar(value=1)   # 第幾張貼圖作為 Main Image
        self.tab_sticker_index = tk.IntVar(value=1)    # 第幾張貼圖作為 Tab Image
        self.scale_percent = tk.IntVar(value=100)  # 圖片縮放百分比（50-150%）
        self.fit_mode = tk.BooleanVar(value=True)  # 適應模式（避免裁切）
        self.show_grid = tk.BooleanVar(value=True)  # 顯示網格線
        self.grid_color = tk.StringVar(value="red")  # 網格線顏色
        self.grid_width = tk.IntVar(value=1)  # 網格線寬度
        self.grid_style = tk.StringVar(value="dash")  # 網格線樣式（solid/dash）
        self.manual_grid = tk.BooleanVar(value=True)  # 手動調整網格線模式（預設啟用）
        self.offset_x = tk.IntVar(value=0)  # 整體網格 X 軸偏移
        self.offset_y = tk.IntVar(value=0)  # 整體網格 Y 軸偏移
        self.fixed_size_mode = tk.BooleanVar(value=False)  # 固定裁切尺寸模式 (370x320)
        self.drag_whole_mode = tk.BooleanVar(value=False)  # 拖曳整體網格模式
        self.remove_bg = tk.BooleanVar(value=False)  # 去背功能
        self.status_text = tk.StringVar(value="就緒")
        self.progress_value = tk.DoubleVar(value=0)
        
        # 圖片預覽
        self.preview_image = None
        self.preview_photo = None
        self.sample_photo = None  # 縮放預覽範例圖片
        
        # 建立 UI
        self.create_widgets()
        
        # 網格線位置偏移量（用於手動調整）
        self.grid_offsets = {
            'vertical': {},  # {col_index: offset_px}
            'horizontal': {}  # {row_index: offset_px}
        }
        
        # 綁定預覽畫布事件
        self.preview_canvas.bind('<Button-1>', self.on_canvas_click)
        self.preview_canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.preview_canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        
        # 拖曳狀態變數
        self.dragging = False
        self.drag_type = None  # 'v' or 'h'
        self.drag_index = None
        self.drag_start_val = 0
        self.drag_start_mouse = 0
        self.current_offset = 0
        
    def reset_grid_positions(self):
        """重置網格線位置"""
        self.grid_offsets = {
            'vertical': {},
            'horizontal': {}
        }
        self.load_preview()
        self.status_text.set("✓ 網格線已重置")
    
    def on_canvas_click(self, event):
        """滑鼠點擊：檢測點擊類型"""
        if not self.input_path.get() or not hasattr(self, 'preview_metrics'):
            return
            
        x, y = event.x, event.y
        
        # 1. 檢測整體拖曳模式
        if self.drag_whole_mode.get():
            self.dragging = True
            self.drag_type = 'whole'
            self.drag_start_mouse = (x, y)
            self.drag_start_val = (self.offset_x.get(), self.offset_y.get())
            self.preview_canvas.config(cursor="fleur")
            self.status_text.set("正在移動整體網格...")
            return

        # 2. 檢測個別線條拖曳模式
        if not self.manual_grid.get():
            return
            
        threshold = 10  # 點擊判定範圍 (px)
        
        metrics = self.preview_metrics
        start_x = metrics['start_x']
        start_y = metrics['start_y']
        # 重新計算預覽中的格子大小（因縮放可能變動）
        preview_cell_w = metrics['cell_w'] * self.preview_scale_ratio 
        # 注意：metrics['cell_w'] 是原始大小，但這裡我們需要計算預覽位置
        # 其實 draw_grid_overlay 計算位置時已經除以 ratio 處理了 visual，我們這裡用簡單方法：
        # 直接遍歷所有線的位置來比對最準確
        
        # 為了簡化，復用之前的邏輯，或是直接反算：
        # 我們知道每條線在 Canvas 上的 X 座標
        global_x = self.offset_x.get()
        global_y = self.offset_y.get()
        cell_w = metrics['cell_w']
        cell_h = metrics['cell_h']
        
        # 檢測垂直線
        cols = self.cols.get()
        closest_dist = threshold
        target_index = -1
        
        for i in range(cols + 1):
            vis_offset = self.grid_offsets['vertical'].get(i, 0)
            
            # 正確的 Canvas X 計算公式（與 draw_grid_overlay 一致）
            # start_x (畫布) + i*cell_w (預覽像素) + global_x/ratio (換算預覽) + offset/ratio (換算預覽)
            line_x = start_x + (i * cell_w) + (global_x / self.preview_scale_ratio) + (vis_offset / self.preview_scale_ratio)
            
            dist = abs(x - line_x)
            if dist < closest_dist:
                closest_dist = dist
                target_index = i
                
        if target_index != -1:
            self.dragging = True
            self.drag_type = 'v'
            self.drag_index = target_index
            self.drag_start_mouse = x
            self.drag_start_val = self.grid_offsets['vertical'].get(target_index, 0)
            self.preview_canvas.config(cursor="sb_h_double_arrow")
            return

        # 檢測水平線
        rows = self.rows.get()
        closest_dist = threshold
        target_index = -1
        
        for i in range(rows + 1):
            vis_offset = self.grid_offsets['horizontal'].get(i, 0)
            
            # 正確的 Canvas Y 計算公式
            line_y = start_y + (i * cell_h) + (global_y / self.preview_scale_ratio) + (vis_offset / self.preview_scale_ratio)
            
            dist = abs(y - line_y)
            if dist < closest_dist:
                closest_dist = dist
                target_index = i
        
        if target_index != -1:
            self.dragging = True
            self.drag_type = 'h'
            self.drag_index = target_index
            self.drag_start_mouse = y
            self.drag_start_val = self.grid_offsets['horizontal'].get(target_index, 0)
            self.preview_canvas.config(cursor="sb_v_double_arrow")
            return

    def on_canvas_drag(self, event):
        """滑鼠拖曳：更新位置"""
        if not self.dragging:
            return
            
        if self.drag_type == 'whole':
            # 計算偏移
            dx_canvas = event.x - self.drag_start_mouse[0]
            dy_canvas = event.y - self.drag_start_mouse[1]
            
            # 轉換為實際像素
            dx_img = dx_canvas * self.preview_scale_ratio
            dy_img = dy_canvas * self.preview_scale_ratio
            
            # 更新變數
            new_x = int(self.drag_start_val[0] + dx_img)
            new_y = int(self.drag_start_val[1] + dy_img)
            
            self.offset_x.set(new_x)
            self.offset_y.set(new_y)
            
            # 頻繁刷新預覽可能會卡頓，這裡我們只更新網格線位置（視覺欺騙），釋放時再刷新圖片
            # 但因為「整體拖曳」應該很直觀，我們嘗試直接刷新預覽（load_preview 已最佳化）
            # 如果太卡，可以切換為只畫線。現在先試圖直接 load_preview
            self.load_preview()
            return
            
        elif self.drag_type == 'v':
            # 計算新的像素偏移
            delta_canvas = event.x - self.drag_start_mouse
            # 轉換為圖片實際像素偏移
            delta_img = delta_canvas * self.preview_scale_ratio
            new_offset = self.drag_start_val + delta_img
            
            # 更新內部數據
            self.grid_offsets['vertical'][self.drag_index] = int(new_offset)
            
            # 因為只有移動一條線，我們可以直接更新線的位置（視覺）
            # 不過因為 load_preview 現在包含了裁切邏輯，為了看到正確的裁切內容，我們還是需要 reload
            # 如果只移動線，使用者看不到這條線對內容的影響，所以全刷新
            self.load_preview()
                
        elif self.drag_type == 'h':
            delta_canvas = event.y - self.drag_start_mouse
            delta_img = delta_canvas * self.preview_scale_ratio
            new_offset = self.drag_start_val + delta_img
            
            self.grid_offsets['horizontal'][self.drag_index] = int(new_offset)
            self.load_preview()

    def on_canvas_release(self, event):
        """釋放滑鼠"""
        if self.dragging:
            self.dragging = False
            self.preview_canvas.config(cursor="")
            self.status_text.set("調整完成")
        
    def create_widgets(self):
        """建立 UI 組件"""
        
        # ===== 標題區 =====
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame,
            text="🎨 LINE 貼圖切割工具",
            font=("Arial", 18, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="精確切割貼圖集為獨立貼圖",
            font=("Arial", 10)
        )
        subtitle_label.pack()
        
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # ===== 主要內容區 =====
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # --- 左側：可滾動的控制面板 ---
        left_outer_frame = ttk.Frame(main_paned)
        main_paned.add(left_outer_frame, weight=0)  # weight=0 固定寬度
        
        # 創建 Canvas 和 Scrollbar
        self.canvas_container = tk.Canvas(left_outer_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_outer_frame, orient="vertical", command=self.canvas_container.yview)
        
        # 創建實際容納控制項的 Frame
        self.left_scroll_frame = ttk.Frame(self.canvas_container)
        self.left_scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas_container.configure(
                scrollregion=self.canvas_container.bbox("all"),
                width=e.width
            )
        )
        
        self.canvas_window = self.canvas_container.create_window((0, 0), window=self.left_scroll_frame, anchor="nw")
        self.canvas_container.configure(yscrollcommand=scrollbar.set)
        
        # 佈局 Scrollbar 和 Canvas
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 綁定滑鼠滾輪
        self._bind_mousewheel(self.canvas_container)
        
        # --- 使用 left_scroll_frame 作為父容器 ---
        left_frame = self.left_scroll_frame
        
        # 輸入文件
        input_group = ttk.LabelFrame(left_frame, text="📂 輸入文件", padding="10")
        input_group.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        ttk.Entry(input_group, textvariable=self.input_path, width=40).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(input_group, text="選擇圖片", command=self.select_input_file).pack(fill=tk.X)
        
        # 輸出目錄
        output_group = ttk.LabelFrame(left_frame, text="💾 輸出目錄", padding="10")
        output_group.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(output_group, textvariable=self.output_dir, width=40).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(output_group, text="選擇目錄", command=self.select_output_dir).pack(fill=tk.X)
        
        # 規格設定
        spec_group = ttk.LabelFrame(left_frame, text="⚙️ 規格設定", padding="10")
        spec_group.pack(fill=tk.X, pady=(0, 10))
        
        # 預設規格選項
        ttk.Checkbutton(
            spec_group,
            text="使用標準貼圖集規格 (2560×1664, 4×5)",
            variable=self.use_line_spec,
            command=self.toggle_spec_mode
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # 貼圖集尺寸
        sheet_size_frame = ttk.Frame(spec_group)
        sheet_size_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(sheet_size_frame, text="貼圖集尺寸:").pack(side=tk.LEFT)
        ttk.Entry(sheet_size_frame, textvariable=self.sheet_width, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(sheet_size_frame, text="×").pack(side=tk.LEFT)
        ttk.Entry(sheet_size_frame, textvariable=self.sheet_height, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(sheet_size_frame, text="px").pack(side=tk.LEFT)
        
        # 行列設定 (自定義切割線)
        grid_frame = ttk.LabelFrame(spec_group, text="✂️ 切割線設定", padding="5")
        grid_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 垂直線控制
        v_frame = ttk.Frame(grid_frame)
        v_frame.pack(fill=tk.X, pady=2)
        ttk.Label(v_frame, text="垂直切割 (X軸):").pack(side=tk.LEFT)
        ttk.Button(v_frame, text="-", width=3, command=lambda: self.adjust_grid('cols', -1)).pack(side=tk.LEFT, padx=5)
        ttk.Label(v_frame, textvariable=self.cols, width=3, anchor="center").pack(side=tk.LEFT)
        ttk.Button(v_frame, text="+", width=3, command=lambda: self.adjust_grid('cols', 1)).pack(side=tk.LEFT, padx=5)
        ttk.Label(v_frame, text="欄").pack(side=tk.LEFT)
        
        # 水平線控制
        h_frame = ttk.Frame(grid_frame)
        h_frame.pack(fill=tk.X, pady=2)
        ttk.Label(h_frame, text="水平切割 (Y軸):").pack(side=tk.LEFT)
        ttk.Button(h_frame, text="-", width=3, command=lambda: self.adjust_grid('rows', -1)).pack(side=tk.LEFT, padx=5)
        ttk.Label(h_frame, textvariable=self.rows, width=3, anchor="center").pack(side=tk.LEFT)
        ttk.Button(h_frame, text="+", width=3, command=lambda: self.adjust_grid('rows', 1)).pack(side=tk.LEFT, padx=5)
        ttk.Label(h_frame, text="列").pack(side=tk.LEFT)
        
        # 計算結果顯示
        self.calc_label = ttk.Label(spec_group, text="", foreground="blue")
        self.calc_label.pack(fill=tk.X, pady=(5, 0))
        self.update_calculation()
        
        # LINE 規格選項
        line_spec_frame = ttk.LabelFrame(spec_group, text="LINE 貼圖規格", padding="5")
        line_spec_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(
            line_spec_frame,
            text=f"✓ 貼圖尺寸: {STICKER_SIZE[0]}×{STICKER_SIZE[1]}px",
            foreground="green",
            font=("Arial", 9)
        ).pack(anchor=tk.W)
        
        ttk.Checkbutton(
            line_spec_frame,
            text=f"添加留白邊距（{STICKER_PADDING}px）",
            variable=self.add_padding
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            line_spec_frame,
            text=f"生成主要圖片（{MAIN_IMAGE_SIZE[0]}×{MAIN_IMAGE_SIZE[1]}px）",
            variable=self.generate_main_image
        ).pack(anchor=tk.W, pady=2)
        
        # Main Image 來源貼圖選擇
        main_source_frame = ttk.Frame(line_spec_frame)
        main_source_frame.pack(fill=tk.X, padx=(20, 0), pady=1)
        ttk.Label(main_source_frame, text="來源貼圖編號：").pack(side=tk.LEFT)
        ttk.Spinbox(main_source_frame, from_=1, to=100, textvariable=self.main_sticker_index, width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Checkbutton(
            line_spec_frame,
            text=f"生成標籤圖片（{TAB_IMAGE_SIZE[0]}×{TAB_IMAGE_SIZE[1]}px）",
            variable=self.generate_tab_image
        ).pack(anchor=tk.W, pady=2)
        
        # Tab Image 來源貼圖選擇
        tab_source_frame = ttk.Frame(line_spec_frame)
        tab_source_frame.pack(fill=tk.X, padx=(20, 0), pady=1)
        ttk.Label(tab_source_frame, text="來源貼圖編號：").pack(side=tk.LEFT)
        ttk.Spinbox(tab_source_frame, from_=1, to=100, textvariable=self.tab_sticker_index, width=5).pack(side=tk.LEFT, padx=2)
        
        # 固定尺寸模式選項
        ttk.Checkbutton(
            line_spec_frame,
            text="🔒 使用固定裁切尺寸 (370×320px)",
            variable=self.fixed_size_mode,
            command=self.load_preview
        ).pack(anchor=tk.W, pady=(5, 2))
        
        # 去背選項
        bg_remove_frame = ttk.LabelFrame(spec_group, text="🧹 去背設定", padding="5")
        bg_remove_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Checkbutton(
            bg_remove_frame,
            text="自動去除背景（切割後去背）",
            variable=self.remove_bg
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Label(
            bg_remove_frame,
            text="💡 首次使用會自動下載 AI 模型（約176MB）",
            font=("Arial", 8),
            foreground="gray"
        ).pack(anchor=tk.W)
        
        # 圖片縮放控制
        scale_group = ttk.LabelFrame(spec_group, text="🔍 圖片大小調整", padding="5")
        scale_group.pack(fill=tk.X, pady=(10, 0))
        
        # 縮放說明
        scale_info_frame = ttk.Frame(scale_group)
        scale_info_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(
            scale_info_frame,
            text="調整最終輸出的貼圖大小：",
            font=("Arial", 9)
        ).pack(side=tk.LEFT)
        
        self.scale_value_label = ttk.Label(
            scale_info_frame,
            text="100%",
            foreground="blue",
            font=("Arial", 9, "bold")
        )
        self.scale_value_label.pack(side=tk.LEFT, padx=5)
        
        # 數字輸入框（新增）
        input_frame = ttk.Frame(scale_group)
        input_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(input_frame, text="輸入百分比：").pack(side=tk.LEFT)
        
        scale_spinbox = ttk.Spinbox(
            input_frame,
            from_=50,
            to=150,
            textvariable=self.scale_percent,
            width=8,
            command=self.update_scale_label
        )
        scale_spinbox.pack(side=tk.LEFT, padx=5)
        scale_spinbox.bind('<Return>', lambda e: self.update_scale_label())
        scale_spinbox.bind('<FocusOut>', lambda e: self.update_scale_label())
        
        ttk.Label(input_frame, text="%").pack(side=tk.LEFT)
        
        # 縮放滑桿
        scale_slider_frame = ttk.Frame(scale_group)
        scale_slider_frame.pack(fill=tk.X)
        
        ttk.Label(scale_slider_frame, text="50%").pack(side=tk.LEFT)
        
        self.scale_slider = ttk.Scale(
            scale_slider_frame,
            from_=50,
            to=150,
            orient=tk.HORIZONTAL,
            variable=self.scale_percent,
            command=self.update_scale_label
        )
        self.scale_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Label(scale_slider_frame, text="150%").pack(side=tk.LEFT)
        
        # 尺寸預覽
        self.scale_preview_label = ttk.Label(
            scale_group,
            text=f"➜ 實際輸出：{STICKER_SIZE[0]}×{STICKER_SIZE[1]}px",
            foreground="green",
            font=("Arial", 8)
        )
        self.scale_preview_label.pack(pady=(5, 0))
        
        # 適應模式選項
        ttk.Checkbutton(
            scale_group,
            text="✓ 智能適應（放大>100%時不裁切，自動縮小以適應370×320）",
            variable=self.fit_mode
        ).pack(anchor=tk.W, pady=(8, 0))
        
        # 網格線設定
        grid_settings_group = ttk.LabelFrame(spec_group, text="📐 預覽網格線設定", padding="5")
        grid_settings_group.pack(fill=tk.X, pady=(10, 0))
        
        # 顯示網格線開關
        ttk.Checkbutton(
            grid_settings_group,
            text="顯示網格線",
            variable=self.show_grid,
            command=self.load_preview
        ).pack(anchor=tk.W, pady=2)
        
        # 顏色選擇
        color_frame = ttk.Frame(grid_settings_group)
        color_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(color_frame, text="顏色：").pack(side=tk.LEFT)
        colors = ["red", "blue", "green", "black", "yellow", "cyan", "magenta"]
        color_combo = ttk.Combobox(
            color_frame,
            textvariable=self.grid_color,
            values=colors,
            width=10,
            state="readonly"
        )
        color_combo.pack(side=tk.LEFT, padx=5)
        color_combo.bind('<<ComboboxSelected>>', lambda e: self.load_preview())
        
        # 粗細選擇
        width_frame = ttk.Frame(grid_settings_group)
        width_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(width_frame, text="粗細：").pack(side=tk.LEFT)
        width_spin = ttk.Spinbox(
            width_frame,
            from_=1,
            to=5,
            textvariable=self.grid_width,
            width=5,
            command=self.load_preview
        )
        width_spin.pack(side=tk.LEFT, padx=5)
        width_spin.bind('<Return>', lambda e: self.load_preview())
        ttk.Label(width_frame, text="px").pack(side=tk.LEFT)
        
        # 樣式選擇
        style_frame = ttk.Frame(grid_settings_group)
        style_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(style_frame, text="樣式：").pack(side=tk.LEFT)
        ttk.Radiobutton(
            style_frame,
            text="虛線",
            variable=self.grid_style,
            value="dash",
            command=self.load_preview
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            style_frame,
            text="實線",
            variable=self.grid_style,
            value="solid",
            command=self.load_preview
        ).pack(side=tk.LEFT)
        
        # 手動調整選項
        ttk.Separator(grid_settings_group, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # 整體平移控制
        offset_frame = ttk.Frame(grid_settings_group)
        offset_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(offset_frame, text="整體平移 (XY軸):", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        
        xy_frame = ttk.Frame(offset_frame)
        xy_frame.pack(fill=tk.X, pady=2)
        
        # X軸
        ttk.Label(xy_frame, text="X (左右):").pack(side=tk.LEFT)
        ttk.Spinbox(
            xy_frame, from_=-500, to=500, textvariable=self.offset_x, width=5,
            command=self.load_preview
        ).pack(side=tk.LEFT, padx=2)
        
        # Y軸
        ttk.Label(xy_frame, text="Y (上下):").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Spinbox(
            xy_frame, from_=-500, to=500, textvariable=self.offset_y, width=5,
            command=self.load_preview
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            xy_frame, text="歸零", width=4,
            command=lambda: [self.offset_x.set(0), self.offset_y.set(0), self.load_preview()]
        ).pack(side=tk.LEFT, padx=10)

        # 個別調整選項
        ttk.Separator(grid_settings_group, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        manual_frame = ttk.Frame(grid_settings_group)
        manual_frame.pack(fill=tk.X, pady=2)
        
        # 拖曳模式選擇
        ttk.Checkbutton(
            manual_frame,
            text="✋ 拖曳移動整體網格",
            variable=self.drag_whole_mode,
            command=lambda: self.manual_grid.set(False) if self.drag_whole_mode.get() else None
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            manual_frame,
            text="🖱️ 啟用個別線條微調",
            variable=self.manual_grid,
            command=lambda: self.drag_whole_mode.set(False) if self.manual_grid.get() else None
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Button(
            manual_frame,
            text="重置",
            command=self.reset_grid_positions,
            width=8
        ).pack(side=tk.RIGHT, padx=5)
        
        # 說明文字
        help_label = ttk.Label(
            grid_settings_group,
            text="💡 啟用後，滑鼠按住預覽區的紅色網格線即可「拖曳調整」位置",
            font=("Arial", 9, "bold"),
            foreground="#d9534f"
        )
        help_label.pack(pady=(5, 0))
        
        # 執行按鈕
        action_group = ttk.Frame(left_frame)
        action_group.pack(fill=tk.X, pady=(10, 0))
        
        self.process_btn = ttk.Button(
            action_group,
            text="🚀 開始切割",
            command=self.process_image,
            style="Accent.TButton"
        )
        self.process_btn.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(
            action_group,
            text="📁 開啟輸出目錄",
            command=self.open_output_dir
        ).pack(fill=tk.X)
        
        # --- 右側：預覽區 ---
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)  # weight=3 佔據更多空間
        
        preview_group = ttk.LabelFrame(right_frame, text="🖼️ 圖片預覽", padding="10")
        preview_group.pack(fill=tk.BOTH, expand=True)
        
        # 預覽畫布
        self.preview_canvas = tk.Canvas(
            preview_group,
            bg="white",
            relief=tk.SUNKEN,
            borderwidth=2
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
    
        # 預覽說明
        self.preview_info_label = ttk.Label(
            preview_group,
            text="選擇圖片後將顯示預覽",
            foreground="gray"
        )
        self.preview_info_label.pack(pady=5)
        
        # ===== 底部狀態欄 =====
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        status_frame = ttk.Frame(self.root, padding="5")
        status_frame.pack(fill=tk.X)
        
        # 狀態文字
        status_label = ttk.Label(status_frame, textvariable=self.status_text)
        status_label.pack(side=tk.LEFT)
        
        # 進度條
        self.progress_bar = ttk.Progressbar(
            status_frame,
            variable=self.progress_value,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

    def _bind_mousewheel(self, widget):
        """綁定滑鼠滾輪事件"""
        def _on_mousewheel(event):
            widget.yview_scroll(int(-1*(event.delta/120)), "units")
        
        widget.bind_all("<MouseWheel>", _on_mousewheel)
        # Linux Support
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))
    
    def adjust_grid(self, axis, value):
        """調整網格數量（嘗試保留現有線條位置）"""
        
        # 1. 記錄當前所有線條的絕對位置
        current_positions = []
        is_rows = (axis == 'rows')
        current_count = self.rows.get() if is_rows else self.cols.get()
        total_size = self.sheet_height.get() if is_rows else self.sheet_width.get()
        offset_dict = self.grid_offsets['horizontal'] if is_rows else self.grid_offsets['vertical']
        
        # 如果是固定尺寸模式，基本單元大小是固定的
        if self.fixed_size_mode.get():
            base_unit = STICKER_SIZE[1] if is_rows else STICKER_SIZE[0]
        else:
            base_unit = total_size / max(current_count, 1)
            
        for i in range(current_count + 1):
            # 計算當前絕對位置: 基本格線 + 個別偏移 + 整體偏移
            # 注意: 我們這裡只關心相對位置保持，整體偏移(offset_x/y)對所有線都一樣，可以忽略
            base_pos = i * base_unit
            offset = offset_dict.get(i, 0)
            abs_pos = base_pos + offset
            current_positions.append(abs_pos)
            
        # 2. 更新數量
        if is_rows:
            new_val = self.rows.get() + value
            if new_val < 1: return # 不允許小於 1
            self.rows.set(new_val)
            new_count = new_val
        else:
            new_val = self.cols.get() + value
            if new_val < 1: return # 不允許小於 1
            self.cols.set(new_val)
            new_count = new_val
            
        # 3. 計算新的基本單元大小
        if self.fixed_size_mode.get():
            new_base_unit = STICKER_SIZE[1] if is_rows else STICKER_SIZE[0]
        else:
            new_base_unit = total_size / max(new_count, 1)
            
        # 4. 反算偏移量以維持位置
        new_offsets = {}
        
        # 處理舊有線條（盡量維持位置）
        for i in range(min(len(current_positions), new_count + 1)):
            target_pos = current_positions[i]
            # 新的基準位置
            new_base = i * new_base_unit
            # 需要的偏移量 = 目標絕對位置 - 新基準位置
            new_offsets[i] = int(target_pos - new_base)
            
        # 如果是新增線條，最後一條線（邊界）可能會被拉到新位置，這是正常的
        # 但如果是減少線條，多餘的偏移量會自動被丟棄
        
        # 更新偏移量字典
        if is_rows:
            self.grid_offsets['horizontal'] = new_offsets
        else:
            self.grid_offsets['vertical'] = new_offsets
        
        self.update_calculation()
        self.load_preview()
        
    def toggle_spec_mode(self):
        """切換規格模式"""
        if self.use_line_spec.get():
            self.rows.set(SHEET_ROWS)
            self.cols.set(SHEET_COLS)
            # 恢復標準時重置位置
            self.reset_grid_positions()
            # 同時清空 offsets 變數
            self.grid_offsets = {'vertical': {}, 'horizontal': {}}
            self.offset_x.set(0)
            self.offset_y.set(0)
        else:
            # 切換到自定義時，預設歸零以便使用者添加
            self.rows.set(1)
            self.cols.set(1)
            self.grid_offsets = {'vertical': {}, 'horizontal': {}}
            
        self.update_calculation()
        self.load_preview()
    
    def update_calculation(self):
        """更新計算結果顯示"""
        try:
            cell_w = self.sheet_width.get() // self.cols.get()
            cell_h = self.sheet_height.get() // self.rows.get()
            total = self.rows.get() * self.cols.get()
            self.calc_label.config(
                text=f"➜ 每格: {cell_w}×{cell_h}px | 總數: {total} 張"
            )
        except:
            self.calc_label.config(text="")
    
    def update_scale_label(self, value=None):
        """更新縮放百分比顯示"""
        scale = self.scale_percent.get()
        self.scale_value_label.config(text=f"{scale}%")
        
        # 計算實際輸出尺寸（固定 370×320，只改變內容大小）
        self.scale_preview_label.config(
            text=f"➜ 輸出：370×320px (內容縮放：{scale}%)"
        )
        
        # 如果已經有圖片，重新載入預覽以顯示縮放效果
        if self.input_path.get():
            self.load_preview()
    
    def select_input_file(self):
        """選擇輸入文件"""
        filename = filedialog.askopenfilename(
            title="選擇貼圖集圖片",
            filetypes=[
                ("PNG 圖片", "*.png"),
                ("所有圖片", "*.png *.jpg *.jpeg"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.input_path.set(filename)
            self.load_preview()
            self.status_text.set(f"已選擇: {Path(filename).name}")
    
    def select_output_dir(self):
        """選擇輸出目錄"""
        dirname = filedialog.askdirectory(title="選擇輸出目錄")
        if dirname:
            self.output_dir.set(dirname)
            self.status_text.set(f"輸出至: {dirname}")
    
    def get_sorted_markers(self, total_size, count, offsets):
        """
        計算並返回排序後的網格切割線位置 (原圖座標)
        
        Args:
            total_size: 總長度 (寬或高)
            count: 格子數量 (rows 或 cols)
            offsets: 偏移量字典 {index: offset}
            
        Returns:
            list: 排序後的像素位置列表 [0, pos1, pos2, ..., total_size]
        """
        markers = []
        
        is_vertical = (offsets is self.grid_offsets['vertical'])
        
        if self.fixed_size_mode.get():
            cell_size = STICKER_SIZE[0] if is_vertical else STICKER_SIZE[1]
        else:
            cell_size = total_size / max(count, 1)
            
        for i in range(count + 1):
            base_pos = i * cell_size
            offset = offsets.get(i, 0)
            markers.append(int(base_pos + offset))
            
        markers.sort()
        return markers

    def load_preview(self):
        """載入並顯示預覽"""
        if not self.input_path.get():
            return
        
        try:
            # 載入圖片
            img = Image.open(self.input_path.get())
            
            # 取得縮放百分比
            scale_percent = self.scale_percent.get()
            
            # 處理每個格子的內容縮放（與實際切割一致）
            if scale_percent != 100 or self.fixed_size_mode.get() or True: # 強制使用新邏輯
                # 獲取行列數
                rows = self.rows.get()
                cols = self.cols.get()
                
                # 獲取排序後的切割線位置
                # 注意：這邊不包含整體偏移 (offset_x, offset_y)，因為那是最後 crop 時加的
                # 但為了邏輯一致，我們應該要把整體偏移視為對 image 的平移，或者對所有線的平移
                # 為了避免複雜，我們採取：計算出的 markers 是相對於 (0,0) 的位置
                
                # 修正：get_sorted_markers 回傳的是未加整體偏移的位置
                col_markers = self.get_sorted_markers(img.width, cols, self.grid_offsets['vertical'])
                row_markers = self.get_sorted_markers(img.height, rows, self.grid_offsets['horizontal'])
                
                # 創建新畫布（維持原始尺寸）
                processed_img = Image.new('RGBA', (img.width, img.height), (255, 255, 255, 0))
                
                # 整體偏移
                global_x = self.offset_x.get()
                global_y = self.offset_y.get()
                
                # 對每個格子應用內容縮放
                for r in range(rows):
                    for c in range(cols):
                        # 確保不超出 markers 範圍
                        if r >= len(row_markers) - 1 or c >= len(col_markers) - 1:
                            continue
                            
                        # 取得當前格子的相對座標 (由排序後的 markers 決定)
                        # 並加上整體偏移
                        left = col_markers[c] + global_x
                        top = row_markers[r] + global_y
                        right = col_markers[c+1] + global_x
                        bottom = row_markers[r+1] + global_y
                        
                        # 確保座標合理（雖然 sort 解決了順序，但可能超出圖片範圍或是寬度為0）
                        if right <= left or bottom <= top:
                            continue
                            
                        # 裁切格子
                        try:
                            # 注意：crop 接受的座標可以是 float，但最好轉 int
                            cell = img.crop((int(left), int(top), int(right), int(bottom)))
                        except Exception:
                            continue
                            
                        cell_width = cell.width
                        cell_height = cell.height
                        
                        if cell_width <= 0 or cell_height <= 0:
                            continue
                        
                        # 計算縮放後的內容尺寸
                        if self.fixed_size_mode.get():
                             # 固定模式：內容依照 370x320 縮放? 還是內容不動?
                             # 依照之前的邏輯：百分比縮放
                             # 這裡假設固定模式是指「輸出格子」是 370x320
                             # 但如果裁切下來的不是 370x320 呢？
                             # Prompt: "The grid cells should have a fixed size (370x320px)"
                             # 這邊我們維持內容縮放邏輯
                             target_w = STICKER_SIZE[0]
                             target_h = STICKER_SIZE[1]
                        else:
                             target_w = cell_width
                             target_h = cell_height

                        content_w = int(target_w * scale_percent / 100)
                        content_h = int(target_h * scale_percent / 100)
                        
                        # 縮放內容
                        if content_w > 0 and content_h > 0:
                            content_scaled = cell.resize((content_w, content_h), Image.Resampling.LANCZOS)
                            
                            # 創建格子大小的畫布 (用來貼回預覽圖)
                            # 預覽圖上，這個格子應該佔多大？
                            # 應該是佔用 markers 定義的大小
                            cell_canvas = Image.new('RGBA', (cell_width, cell_height), (255, 255, 255, 0))
                            
                            # 計算置中位置
                            paste_x = (cell_width - content_w) // 2
                            paste_y = (cell_height - content_h) // 2
                            
                            # 貼上縮放後的內容
                            if content_scaled.mode == 'RGBA':
                                cell_canvas.paste(content_scaled, (paste_x, paste_y), content_scaled)
                            else:
                                cell_canvas.paste(content_scaled, (paste_x, paste_y))
                            
                            # 貼回到整體畫布
                            processed_img.paste(cell_canvas, (int(left), int(top)))
                
                preview_img = processed_img
            else:
                preview_img = img
            
            # 計算縮放比例以適應畫布
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width <= 1:
                canvas_width = 400
            if canvas_height <= 1:
                canvas_height = 400
            
            # 縮放到適應畫布（保持長寬比）
            img_ratio = preview_img.width / preview_img.height
            canvas_ratio = canvas_width / canvas_height
            
            if img_ratio > canvas_ratio:
                new_width = canvas_width - 60
                new_height = int(new_width / img_ratio)
            else:
                new_height = canvas_height - 60
                new_width = int(new_height * img_ratio)
            
            # 保存預覽縮放比例（用於滑鼠拖曳計算）
            self.preview_scale_ratio = img.width / new_width
            
            # 預覽圖片
            img_resized = preview_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(img_resized)
            
            # 顯示在畫布上
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self.preview_photo,
                anchor=tk.CENTER
            )
            
            # 繪製網格線
            self.draw_grid_overlay(new_width, new_height, canvas_width, canvas_height)
            
            # 顯示資訊
            if scale_percent < 100:
                info_text = f"內容縮放：{scale_percent}% | 留白增加 | 輸出：370×320px"
            elif scale_percent > 100:
                info_text = f"內容放大：{scale_percent}% | 留白減少 | 輸出：370×320px"
            else:
                info_text = f"標準尺寸：100% | 輸出：370×320px"
            
            self.preview_canvas.create_rectangle(
                10, 10, 320, 50,
                fill='white',
                outline='blue',
                width=2
            )
            self.preview_canvas.create_text(
                165, 30,
                text=info_text,
                fill='blue',
                font=('Arial', 9, 'bold')
            )
            
        except Exception as e:
            messagebox.showerror("錯誤", f"無法載入預覽:\n{str(e)}")
    
    def draw_grid_overlay(self, img_width, img_height, canvas_width, canvas_height):
        """在預覽上繪製網格線"""
        # 檢查是否顯示網格線
        if not self.show_grid.get():
            return
        
        rows = self.rows.get()
        cols = self.cols.get()
        
        # 取得網格線設定
        grid_color = self.grid_color.get()
        grid_width = self.grid_width.get()
        grid_style = self.grid_style.get()
        
        # 設定虛線樣式
        if grid_style == "dash":
            dash_pattern = (4, 4)
        else:
            dash_pattern = None
        
        # 計算起始位置（居中）
        start_x = (canvas_width - img_width) // 2
        start_y = (canvas_height - img_height) // 2
        
        # 繪製網格
        if self.fixed_size_mode.get():
            cell_w = STICKER_SIZE[0]
            cell_h = STICKER_SIZE[1]
        else:
            cell_w = img_width / cols if cols > 0 else img_width
            cell_h = img_height / rows if rows > 0 else img_height
        
        # 取得整體偏移
        global_x = self.offset_x.get()
        global_y = self.offset_y.get()
        
        # 垂直線
        for i in range(cols + 1):
            # 計算基本位置 (原圖座標)
            if self.fixed_size_mode.get():
                base_x_orig = i * STICKER_SIZE[0]
            else:
                base_x_orig = i * (img_width * self.preview_scale_ratio / cols if cols > 0 else 0)
            
            # 取得個別偏移 (原圖座標)
            vis_offset = self.grid_offsets['vertical'].get(i, 0)
            
            # 計算最終位置 (原圖座標)
            total_x_orig = base_x_orig + global_x + vis_offset
            
            # 轉換為預覽畫布座標
            x = start_x + (total_x_orig / self.preview_scale_ratio)
            
            self.preview_canvas.create_line(
                x, start_y,
                x, start_y + img_height,
                fill=grid_color,
                width=grid_width,
                dash=dash_pattern,
                tags=('grid', f'v_{i}')
            )
        
        # 水平線
        for i in range(rows + 1):
            # 計算基本位置 (原圖座標)
            if self.fixed_size_mode.get():
                base_y_orig = i * STICKER_SIZE[1]
            else:
                base_y_orig = i * (img_height * self.preview_scale_ratio / rows if rows > 0 else 0)
            
            # 取得個別偏移 (原圖座標)
            vis_offset = self.grid_offsets['horizontal'].get(i, 0)
            
            # 計算最終位置 (原圖座標)
            total_y_orig = base_y_orig + global_y + vis_offset
            
            # 轉換為預覽畫布座標
            y = start_y + (total_y_orig / self.preview_scale_ratio)
            
            self.preview_canvas.create_line(
                start_x, y,
                start_x + img_width, y,
                fill=grid_color,
                width=grid_width,
                dash=dash_pattern,
                tags=('grid', f'h_{i}')
            )
        
        # 保存畫布與圖片的相對位置參數，供滑鼠事件使用
        self.preview_metrics = {
            'start_x': start_x,
            'start_y': start_y,
            'img_width': img_width,
            'img_height': img_height,
            'cell_w': cell_w,
            'cell_h': cell_h
        }
    
    def open_output_dir(self):
        """開啟輸出目錄"""
        output_path = Path(self.output_dir.get())
        if output_path.exists():
            os.startfile(output_path)
        else:
            messagebox.showwarning("警告", "輸出目錄不存在")
    
    def process_image(self):
        """處理圖片（在背景執行緒）"""
        if not self.input_path.get():
            messagebox.showwarning("警告", "請先選擇輸入圖片")
            return
        
        # 在背景執行緒執行
        thread = threading.Thread(target=self.process_image_thread)
        thread.daemon = True
        thread.start()
    
    def process_image_thread(self):
        """處理圖片的實際邏輯"""
        try:
            # 更新 UI
            self.process_btn.config(state=tk.DISABLED)
            self.status_text.set("正在處理...")
            self.progress_value.set(0)
            
            # 執行切割
            result = self.split_stickers()
            
            # 完成
            self.progress_value.set(100)
            self.status_text.set(f"✓ 完成！已切割 {result['count']} 張貼圖")
            
            # 顯示結果
            extras_info = []
            if result.get('has_main'):
                extras_info.append("✓ 主要圖片 (main.png)")
            if result.get('has_tab'):
                extras_info.append("✓ 標籤圖片 (tab.png)")
            
            extras_text = "\n".join(extras_info) if extras_info else ""
            
            # 顯示縮放資訊
            scale_percent = self.scale_percent.get()
            
            message = f"成功切割 {result['count']} 張貼圖！\n\n"
            message += f"輸出尺寸：370×320px (固定)\n"
            if scale_percent != 100:
                message += f"內容縮放：{scale_percent}%\n"
            if self.remove_bg.get():
                message += f"去背：✓ 已啟用\n"
            message += "\n"
            if extras_text:
                message += f"額外生成：\n{extras_text}\n\n"
            message += f"輸出目錄：\n{result['output_dir']}\n\n"
            message += f"總耗時：{result['time']:.2f} 秒"
            
            self.root.after(0, lambda: messagebox.showinfo("完成", message))
            
        except Exception as e:
            self.status_text.set(f"✗ 錯誤: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("錯誤", f"處理失敗:\n{str(e)}"))
        
        finally:
            self.process_btn.config(state=tk.NORMAL)
    
    def split_stickers(self):
        """切割貼圖的核心邏輯"""
        import time
        start_time = time.time()
        
        # 開啟圖片
        img = Image.open(self.input_path.get())
        
        # 取得參數
        rows = self.rows.get()
        cols = self.cols.get()
        output_dir = Path(self.output_dir.get())
        add_padding = self.add_padding.get()
        scale_percent = self.scale_percent.get()
        
        # 建立輸出目錄
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 計算每個單元格的尺寸 & 切割線位置
        col_markers = self.get_sorted_markers(img.width, cols, self.grid_offsets['vertical'])
        row_markers = self.get_sorted_markers(img.height, rows, self.grid_offsets['horizontal'])
        
        # 整體偏移 (最後 crop 時統一加)
        global_x = self.offset_x.get()
        global_y = self.offset_y.get()
        
        total = rows * cols
        count = 0
        stickers_for_extras = {}  # {index: PIL Image} 儲存需要的貼圖
        main_idx = self.main_sticker_index.get()
        tab_idx = self.tab_sticker_index.get()
        
        # 切割圖片
        for row in range(rows):
            for col in range(cols):
                count += 1
                
                # 更新進度
                progress = (count / total) * 50  # 前 50% 用於切割
                self.progress_value.set(progress)
                
                # 確保不超出 markers 範圍
                if row >= len(row_markers) - 1 or col >= len(col_markers) - 1:
                    continue

                # 計算裁切區域（基於排序後的 markers + 整體偏移）
                left = col_markers[col] + global_x
                top = row_markers[row] + global_y
                right = col_markers[col+1] + global_x
                bottom = row_markers[row+1] + global_y
                
                # 裁切（現在座標保證是排序過的，只要 right > left 即可）
                # 注意：如果 right <= left，可能是因為線條重疊，crop 會報錯或空，加個檢查
                if right <= left: right = left + 1 
                if bottom <= top: bottom = top + 1
                
                try:
                    sticker = img.crop((int(left), int(top), int(right), int(bottom)))
                except Exception as e:
                    print(f"Error cropping: {e}")
                    sticker = Image.new('RGBA', (STICKER_SIZE[0], STICKER_SIZE[1]), (255, 255, 255, 0))
                
                # 添加留白（如果啟用）
                if add_padding:
                    sticker_with_padding = self.add_padding_to_image(sticker, STICKER_PADDING)
                else:
                    sticker_with_padding = sticker
                
                # 應用縮放百分比到內容（輸出尺寸固定 370×320）
                is_scaling = (scale_percent != 100 or self.fixed_size_mode.get() or True)
                
                if is_scaling:
                    # 計算縮放後的內容尺寸
                    if self.fixed_size_mode.get():
                        # 固定模式：內容依照 370x320 為基準縮放
                        target_w = STICKER_SIZE[0]
                        target_h = STICKER_SIZE[1]
                    else:
                        # 非固定模式：以實際裁切大小為基準
                        target_w = sticker_with_padding.width
                        target_h = sticker_with_padding.height
                        
                    content_width = int(target_w * scale_percent / 100)
                    content_height = int(target_h * scale_percent / 100)
                    
                    if content_width <= 0: content_width = 1
                    if content_height <= 0: content_height = 1
                    
                    # 縮放內容
                    content_scaled = sticker_with_padding.resize((content_width, content_height), Image.Resampling.LANCZOS)
                    
                    # 創建固定尺寸的透明畫布 (370×320)
                    sticker_resized = Image.new('RGBA', STICKER_SIZE, (255, 255, 255, 0))
                    
                    # 檢查是否啟用適應模式
                    fit_mode = self.fit_mode.get()
                    
                    if fit_mode and (content_width > STICKER_SIZE[0] or content_height > STICKER_SIZE[1]):
                        # 適應模式：縮小以適應框架
                        ratio = min(STICKER_SIZE[0] / content_width, STICKER_SIZE[1] / content_height)
                        fitted_width = int(content_width * ratio)
                        fitted_height = int(content_height * ratio)
                        if fitted_width <= 0: fitted_width = 1
                        if fitted_height <= 0: fitted_height = 1
                        content_fitted = content_scaled.resize((fitted_width, fitted_height), Image.Resampling.LANCZOS)
                        
                        paste_x = (STICKER_SIZE[0] - fitted_width) // 2
                        paste_y = (STICKER_SIZE[1] - fitted_height) // 2
                        
                        if content_fitted.mode == 'RGBA':
                            sticker_resized.paste(content_fitted, (paste_x, paste_y), content_fitted)
                        else:
                            sticker_resized.paste(content_fitted, (paste_x, paste_y))
                    else:
                        # 一般模式：直接置中
                        paste_x = (STICKER_SIZE[0] - content_width) // 2
                        paste_y = (STICKER_SIZE[1] - content_height) // 2
                        
                        if content_scaled.mode == 'RGBA':
                             # 注意：PIL paste 超出邊界會自動裁切，這是預期行為
                            sticker_resized.paste(content_scaled, (paste_x, paste_y), content_scaled)
                        else:
                            sticker_resized.paste(content_scaled, (paste_x, paste_y))
                else:
                    sticker_resized = sticker_with_padding.resize(STICKER_SIZE, Image.Resampling.LANCZOS)
                
                # 去背處理
                if self.remove_bg.get():
                    self.status_text.set(f"正在去背 {count}/{total}...")
                    from rembg import remove
                    sticker_resized = remove(sticker_resized)
                
                # 儲存
                output_path = output_dir / f"sticker_{count:02d}.png"
                sticker_resized.save(output_path, 'PNG', optimize=True)
                
                # 儲存指定貼圖用於生成 Main/Tab 圖片
                if count == main_idx or count == tab_idx:
                    stickers_for_extras[count] = sticker_resized.copy()
        
        # 生成主要圖片（Main Image）
        if self.generate_main_image.get() and main_idx in stickers_for_extras:
            self.progress_value.set(60)
            main_img = self.create_main_image(stickers_for_extras[main_idx])
            main_path = output_dir / "main.png"
            main_img.save(main_path, 'PNG', optimize=True)
        
        # 生成標籤圖片（Tab Image）
        if self.generate_tab_image.get() and tab_idx in stickers_for_extras:
            self.progress_value.set(70)
            tab_img = self.create_tab_image(stickers_for_extras[tab_idx])
            tab_path = output_dir / "tab.png"
            tab_img.save(tab_path, 'PNG', optimize=True)
        
        elapsed_time = time.time() - start_time
        
        return {
            'count': count,
            'output_dir': str(output_dir.absolute()),
            'time': elapsed_time,
            'has_main': self.generate_main_image.get(),
            'has_tab': self.generate_tab_image.get()
        }
    
    def add_padding_to_image(self, img, padding):
        """
        為圖片添加留白邊距
        
        Args:
            img: PIL Image 對象
            padding: 留白像素數
            
        Returns:
            添加留白後的圖片
        """
        # 創建新的透明畫布（比原圖大）
        new_width = img.width - (padding * 2)
        new_height = img.height - (padding * 2)
        
        # 確保尺寸為正數
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
    
    def create_main_image(self, sticker_img):
        """
        創建主要圖片（Main Image）- 用於貼圖商店展示
        
        Args:
            sticker_img: 第一張貼圖的 PIL Image 對象
            
        Returns:
            240×240 的主要圖片
        """
        # 調整為正方形 240×240
        main_img = sticker_img.resize(MAIN_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # 如果不是 RGBA，轉換為 RGBA
        if main_img.mode != 'RGBA':
            main_img = main_img.convert('RGBA')
        
        return main_img
    
    def create_tab_image(self, sticker_img):
        """
        創建聊天室標籤圖片（Tab Image）- 用於聊天室貼圖選單
        
        Args:
            sticker_img: 第一張貼圖的 PIL Image 對象
            
        Returns:
            96×74 的標籤圖片
        """
        # 調整為 96×74
        tab_img = sticker_img.resize(TAB_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # 如果不是 RGBA，轉換為 RGBA
        if tab_img.mode != 'RGBA':
            tab_img = tab_img.convert('RGBA')
        
        return tab_img

    def on_window_resize(self, event):
        """處理視窗縮放"""
        if event.widget == self.canvas_container:
            canvas_width = event.width
            self.canvas_container.itemconfig(self.canvas_window, width=canvas_width)

def main():
    """主程式"""
    root = tk.Tk()
    app = StickerSplitterGUI(root)
    
    # 綁定 Canvas resize 事件
    app.canvas_container.bind('<Configure>', app.on_window_resize)
    
    # 設定最小視窗大小
    root.minsize(1000, 700)
    root.mainloop()

if __name__ == "__main__":
    main()
