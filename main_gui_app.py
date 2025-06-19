import json
import tkinter as tk
from tkinter import messagebox
import subprocess

# 全局變量，用於儲存當前模式（light/dark）和顏色
current_mode = "light"
bg_color = "white"
fg_color = "black"

# 錯誤類型變數字典
error_vars = {}

def load_data(filename):
    """
    載入指定 JSON 檔案的資料。
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"已從 '{filename}' 載入 {len(data)} 筆資料。")
            return data
    except FileNotFoundError:
        messagebox.showerror("錯誤", f"找不到 '{filename}' 檔案，請確保檔案存在。")
        return []
    except json.JSONDecodeError:
        messagebox.showerror("錯誤", f"'{filename}' 檔案格式不正確或為空，請檢查。")
        return []

def get_first_unconfirmed_index(data):
    """
    從資料中找到第一個狀態不是「確認」的題目的索引。
    """
    for i, item in enumerate(data):
        status = item.get('status', [])
        # 如果狀態列表不包含"確認"，或者包含"確認"但還有其他錯誤類型，都視為未確認
        if not ("確認" in status and len(status) == 1):
            return i
    return 0 # 如果所有題目都已確認，從頭開始

def get_saved_status(data, question_to_find):
    """
    根據 total_question_number 查找題目並返回其狀態。
    此函數在 display_question 內部被簡化，直接從 question_item 中讀取。
    但為了完整性，若需要獨立查找，可保留。
    """
    for item in data:
        if item.get('total_question_number') == question_to_find.get('total_question_number'):
            return item['status']
    return None

def save_result(status, question_item_to_save):
    """
    呼叫 main_gui_app_save.py 腳本來保存結果。
    將整個題目物件和狀態傳遞給 main_gui_app_save.py。
    """
    # 將 Python 物件轉換為 JSON 字串
    status_json_str = json.dumps(status, ensure_ascii=False)
    question_item_json_str = json.dumps(question_item_to_save, ensure_ascii=False)

    try:
        # 調用 main_gui_app_save.py，並傳遞 JSON 字串作為參數
        result = subprocess.run(
            ["python", "main_gui_app_save.py", status_json_str, question_item_json_str],
            check=True, # 檢查返回碼，非零則拋出 CalledProcessError
            capture_output=True, # 捕獲標準輸出和標準錯誤
            text=True, # 將輸出視為文本
            encoding='utf-8' # 指定編碼
        )
        print("main_gui_app_save.py 輸出:", result.stdout)
        if result.stderr:
            print("main_gui_app_save.py 錯誤輸出:", result.stderr)
        messagebox.showinfo("儲存成功", "資料已儲存！")
    except subprocess.CalledProcessError as e:
        print(f"執行 main_gui_app_save.py 時發生錯誤: {e.stderr}")
        messagebox.showerror("錯誤", f"保存失敗：\n{e.stderr}")
    except FileNotFoundError:
        print("錯誤：找不到 main_gui_app_save.py 檔案。")
        messagebox.showerror("錯誤", "找不到 'main_gui_app_save.py' 檔案，請確保它在同一個目錄中。")
    except Exception as e:
        print(f"調用 main_gui_app_save.py 時發生未知錯誤: {e}")
        messagebox.showerror("錯誤", f"調用 'main_gui_app_save.py' 時發生未知錯誤：\n{e}")

def toggle_mode():
    """
    切換光暗模式。
    """
    global current_mode, bg_color, fg_color
    current_mode = "dark" if current_mode == "light" else "light"
    bg_color = "black" if current_mode == "dark" else "white"
    fg_color = "white" if current_mode == "dark" else "black"
    apply_colors()
    # 重新顯示題目以應用新顏色，確保所有元件顏色正確更新
    display_question(main_data, current_question_index)

def apply_colors():
    """
    應用當前模式的顏色到所有 Tkinter 元件。
    """
    window.config(bg=bg_color)
    if mode_button:
        mode_button.config(fg=fg_color, bg=bg_color)
    # 這裡的迭代可能不會更新 canvas 內的 frame，所以 display_question 會重新繪製
    # 但對於頂層部件，這仍然是有用的
    for widget in window.winfo_children():
        if isinstance(widget, (tk.Frame, tk.Label, tk.Checkbutton, tk.Button, tk.Canvas)):
            try:
                # 按鈕的文字顏色通常希望保持清晰對比
                widget.config(bg=bg_color, fg=fg_color if not isinstance(widget, tk.Button) else "black")
            except tk.TclError:
                pass # 某些元件可能沒有fg屬性，忽略錯誤

def display_question(data, question_index):
    """
    顯示指定索引的題目內容。
    """
    global error_vars, current_question_index, main_data # 需要在函數內修改全局變量

    # 確保索引在有效範圍內
    if not (0 <= question_index < len(data)):
        messagebox.showinfo("結束", "所有題目已完成或索引無效。")
        window.destroy()
        return

    current_question_index = question_index # 更新當前題目索引
    question_item = data[question_index] # 獲取整個題目項目 (包含 total_question_number, status, question_data)
    question = question_item['question_data'] # 獲取實際的題目內容
    total_q_num_display = question_item.get('total_question_number', question_index + 1) # 顯示 total_question_number

    # 清除舊的內容 (除了模式切換按鈕)
    for widget in window.winfo_children():
        if widget != mode_button:
            widget.destroy()

    apply_colors()

    # 建立 Canvas 和 Scrollbar
    canvas = tk.Canvas(window, bg=bg_color, highlightthickness=0)
    scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=bg_color)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # 滑鼠滾輪事件
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # 定義統一的左側內邊距
    LEFT_PADX = 50 

    # === 顯示題目資訊 ===
    info_frame = tk.Frame(scrollable_frame, bg=bg_color)
    info_frame.pack(pady=10, anchor='w', padx=LEFT_PADX)
    tk.Label(info_frame, text=f"學校: {question['school']}", fg=fg_color, bg=bg_color).pack(anchor='w')
    tk.Label(info_frame, text=f"科系: {question['department']}", fg=fg_color, bg=bg_color).pack(anchor='w')
    tk.Label(info_frame, text=f"年份: {question['year']}", fg=fg_color, bg=bg_color).pack(anchor='w')
    tk.Label(info_frame, text=f"題號: {question['question_number']} (總題號: {total_q_num_display}) ({question_index + 1}/{len(data)})", fg=fg_color, bg=bg_color).pack(anchor='w')

    # 題目文字
    question_label = tk.Label(scrollable_frame, text="題目: " + question['question_text'], fg=fg_color, bg=bg_color, wraplength=500, justify='left')
    question_label.pack(pady=10, anchor='w', padx=LEFT_PADX)

    # 選項區
    options_frame = tk.Frame(scrollable_frame, bg=bg_color)
    options_frame.pack(pady=5, anchor='w', padx=LEFT_PADX)
    tk.Label(options_frame, text="選項：", fg=fg_color, bg=bg_color).pack(anchor='w')
    if 'options' in question and isinstance(question['options'], list) and question['options']:
        for option in question['options']:
            tk.Label(options_frame, text=option, fg=fg_color, bg=bg_color, wraplength=500, justify='left').pack(anchor='w')
    else:
        tk.Label(options_frame, text="（此題沒有選項）", fg="gray", bg=bg_color).pack(anchor='w')

    # 圖片路徑
    image_frame = tk.Frame(scrollable_frame, bg=bg_color)
    image_frame.pack(pady=10, anchor='w', padx=LEFT_PADX)

    tk.Label(image_frame, text="圖片路徑：", fg=fg_color, bg=bg_color).pack(anchor='w')
    if question['image_file']:
        image_filename = question['image_file'][0]
        tk.Label(image_frame, text=f"{image_filename}", fg=fg_color, bg=bg_color).pack(anchor='w')
    else:
        tk.Label(image_frame, text="（此題沒有圖片路徑）", fg="gray", bg=bg_color).pack(anchor='w')

    # 狀態顯示和預設勾選框
    saved_status = question_item.get('status', ['未標記']) # 直接從當前 item 讀取 status
    
    if "確認" in saved_status and len(saved_status) == 1:
        tk.Label(scrollable_frame, text="狀態: 確認", fg="green", bg=bg_color).pack(pady=5, anchor='w', padx=LEFT_PADX)
    else:
        status_str = "、".join(saved_status)
        tk.Label(scrollable_frame, text=f"狀態: {status_str}", fg="red", bg=bg_color).pack(pady=5, anchor='w', padx=LEFT_PADX)

    # === 新增一個框架用於包裹 Checkbutton ===
    checkbox_frame = tk.Frame(scrollable_frame, bg=bg_color)
    checkbox_frame.pack(fill='x', padx=LEFT_PADX, pady=10, anchor='w') 

    # 初始化 error_vars 並根據 saved_status 預設勾選狀態
    error_vars = {
        "題號錯誤": tk.BooleanVar(),
        "題目錯誤": tk.BooleanVar(),
        "選項錯誤": tk.BooleanVar(),
        "圖片錯誤": tk.BooleanVar(),
        "路徑錯誤": tk.BooleanVar(),
    }
    for label, var in error_vars.items():
        if label in saved_status:
            var.set(True) # 預設勾選之前保存的錯誤狀態
        # 將 Checkbutton pack 到新的 checkbox_frame 中
        tk.Checkbutton(checkbox_frame, text=label, variable=var, bg=bg_color, fg=fg_color, selectcolor="gray").pack(anchor='w')


    def correct_answer():
        # 更新 main_data 中的該題目狀態為 "確認"
        question_item['status'] = ["確認"]
        # 這裡的 save_result 傳遞的是整個 question_item，因為 main_gui_app_save.py 需要 total_question_number
        save_result(["確認"], question_item) 
        # 立即更新顯示，並移動到下一題
        display_question(main_data, current_question_index + 1) 

    def incorrect_answer():
        selected_errors = [key for key, var in error_vars.items() if var.get()]
        if not selected_errors:
            messagebox.showwarning("警告", "請至少選擇一個錯誤類型。")
            return
        
        # 更新 main_data 中的該題目狀態為選定的錯誤
        question_item['status'] = selected_errors
        save_result(selected_errors, question_item) # 傳遞整個題目項目
        # 立即更新顯示，並移動到下一題
        display_question(main_data, current_question_index + 1)

    def previous_question():
        global current_question_index
        if current_question_index > 0:
            display_question(data, current_question_index - 1)
        else:
            messagebox.showinfo("提示", "這已經是第一題了。")

    def next_question_action():
        global current_question_index
        if current_question_index < len(data) - 1:
            display_question(data, current_question_index + 1)
        else:
            messagebox.showinfo("結束", "所有題目已完成。")
            window.destroy()

    # 按鈕
    btn_frame = tk.Frame(scrollable_frame, bg=bg_color)
    # 按鈕框架可以居中，或者如果你希望它們也靠左對齊，可以加上 anchor='w' 和 padx
    btn_frame.pack(pady=10) # 保持按鈕居中
    tk.Button(btn_frame, text="儲存錯誤並下一題", command=incorrect_answer, fg="black", bg="white").pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="確認無誤並下一題", command=correct_answer, fg="black", bg="white").pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="上一題", command=previous_question, fg="black", bg="white").pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="下一題", command=next_question_action, fg="black", bg="white").pack(side=tk.LEFT, padx=10)


# --- 主程式入口 ---
if __name__ == "__main__":
    main_data = load_data('check_exam_output.json') # 從 check_exam_output.json 載入

    if not main_data:
        messagebox.showerror("錯誤", "未能載入題目資料，程式將結束。")
        exit()

    window = tk.Tk()
    window.title("題目檢查工具")
    window.geometry("800x700") # 調整視窗大小以容納更多內容
    window.attributes("-topmost", True) # 視窗保持在最上層

    # 初始化模式和顏色
    current_mode = "light"
    bg_color = "white"
    fg_color = "black"

    # 模式切換按鈕
    mode_button = tk.Button(window, text="切換模式", command=toggle_mode, fg=fg_color, bg=bg_color)
    mode_button.pack(side=tk.TOP, anchor=tk.NE, padx=10, pady=10)

    # 找到第一個未確認題目的索引
    current_question_index = get_first_unconfirmed_index(main_data)

    display_question(main_data, current_question_index)
    window.mainloop()