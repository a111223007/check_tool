import json
import tkinter as tk
from tkinter import messagebox
import subprocess

def load_checked_data():
    try:
        with open('check_exam_output.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("警告：找不到 'check_exam_output.json' 檔案，使用空資料。")
        return []
    except json.JSONDecodeError:
        print("警告：'check_exam_output.json' 為空，使用空資料。")
        return []

def get_last_index(checked_data, question_data):
    for i, question in enumerate(question_data):
        if not any(item.get('question_data') == question for item in checked_data):
            return i
    return len(question_data)

def get_saved_status(checked_data, question):
    for item in checked_data:
        if item.get('question_data') == question:
            return item['status']
    return None

def save_result(status, question):
    status_json = json.dumps(status, ensure_ascii=False)
    question_json = json.dumps(question, ensure_ascii=False)
    question_index_str = str(current_question_index)

    try:
        subprocess.run(
            ["python", "save.py", status_json, question_json, question_index_str],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"執行 save.py 時發生錯誤: {e.stderr}")
    except FileNotFoundError:
        print("錯誤：找不到 save.py 檔案。")

def toggle_mode():
    global current_mode, bg_color, fg_color
    current_mode = "dark" if current_mode == "light" else "light"
    bg_color = "black" if current_mode == "dark" else "white"
    fg_color = "white" if current_mode == "dark" else "black"
    apply_colors()
    display_question(question_data, current_question_index, total_questions, load_checked_data())

def apply_colors():
    window.config(bg=bg_color)
    if mode_button:
        mode_button.config(fg=fg_color, bg=bg_color)

def display_question(question_data, question_index, total_questions, checked_data):
    question = question_data[question_index]
    for widget in window.winfo_children():
        if widget != mode_button:
            widget.destroy()

    apply_colors()

    info_frame = tk.Frame(window, bg=bg_color)
    info_frame.pack(pady=10)

    tk.Label(info_frame, text=f"學校: {question['school']}", fg=fg_color, bg=bg_color).pack()
    tk.Label(info_frame, text=f"科系: {question['department']}", fg=fg_color, bg=bg_color).pack()
    tk.Label(info_frame, text=f"年份: {question['year']}", fg=fg_color, bg=bg_color).pack()
    tk.Label(info_frame, text=f"題號: {question['question_number']} ({question_index + 1}/{total_questions})", fg=fg_color, bg=bg_color).pack()

    # 題目（放在選項前）
    question_label = tk.Label(window, text="題目: " + question['question_text'], fg=fg_color, bg=bg_color, wraplength=500)
    question_label.pack(pady=10)

    # 選項
    options_frame = tk.Frame(window, bg=bg_color)
    options_frame.pack(pady=5)

    tk.Label(options_frame, text="選項：", fg=fg_color, bg=bg_color).pack(anchor='w')
    if 'options' in question and isinstance(question['options'], list) and question['options']:
        for idx, option in enumerate(question['options']):
            option_text = f"{option}"
            tk.Label(options_frame, text=option_text, fg=fg_color, bg=bg_color, wraplength=500, justify='left').pack(anchor='w')
    else:
        tk.Label(options_frame, text="（此題沒有選項）", fg="gray", bg=bg_color).pack(anchor='w')


    if question['image_file']:
        image_filename = question['image_file'][0]
        tk.Label(window, text=f"圖片路徑 : {image_filename}", fg=fg_color, bg=bg_color).pack(pady=10)
    else:
        tk.Label(window, text="圖片 : 沒有圖片", fg=fg_color, bg=bg_color).pack(pady=10)

    # 顯示狀態（支援 list）
    saved_status = get_saved_status(checked_data, question)

    # 優先處理 list 中包含 "確認" 的情況
    if isinstance(saved_status, list):
        if "確認" in saved_status and len(saved_status) == 1:
            # 單一確認：綠色
            tk.Label(window, text="狀態: 確認", fg="green", bg=bg_color).pack(pady=5)
        else:
            # 多個錯誤（含或不含確認）：紅色
            status_str = "、".join(saved_status)
            tk.Label(window, text=f"狀態: {status_str}", fg="red", bg=bg_color).pack(pady=5)
    elif saved_status == "確認":
        tk.Label(window, text=f"狀態: {saved_status}", fg="green", bg=bg_color).pack(pady=5)
    else:
        tk.Label(window, text="狀態: 未標記", fg="orange", bg=bg_color).pack(pady=5)


    button_frame = tk.Frame(window, bg=bg_color)
    button_frame.pack(pady=10)

    # 錯誤類型勾選框
    error_vars = {
        "題號錯誤": tk.BooleanVar(),
        "題目錯誤": tk.BooleanVar(),
        "選項錯誤": tk.BooleanVar(),
        "圖片錯誤": tk.BooleanVar(),
        "路徑錯誤": tk.BooleanVar(),
    }
    for label, var in error_vars.items():
        tk.Checkbutton(button_frame, text=label, variable=var, bg=bg_color, fg=fg_color).pack(anchor='w')

    def correct_answer():
        save_result("確認", question)
        next_question()

    def incorrect_answer():
        selected_errors = [key for key, var in error_vars.items() if var.get()]
        if not selected_errors:
            messagebox.showwarning("警告", "請至少選擇一個錯誤類型。")
            return
        save_result(selected_errors, question)
        next_question()

    def previous_question():
        global current_question_index
        if current_question_index > 0:
            current_question_index -= 1
            display_question(question_data, current_question_index, total_questions, load_checked_data())

    def next_question():
        global current_question_index
        current_question_index += 1
        if current_question_index < len(question_data):
            display_question(question_data, current_question_index, total_questions, load_checked_data())
        else:
            messagebox.showinfo("結束", "所有題目已完成。")
            window.destroy()

    # 按鈕

    tk.Button(button_frame, text="儲存錯誤並下一題", command=incorrect_answer, fg="black", bg="white").pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="正確", command=correct_answer, fg="black", bg="white").pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="上一題", command=previous_question, fg="black", bg="white").pack(side=tk.LEFT, padx=10)

# 主程式入口
if __name__ == "__main__":
    try:
        with open('new_exam_output.json', 'r', encoding='utf-8') as f:
            question_data = json.load(f)
    except FileNotFoundError:
        print("錯誤：找不到 'new_exam_output.json' 檔案。")
        exit()
    except json.JSONDecodeError:
        print("錯誤：'new_exam_output.json' 檔案格式不正確。")
        exit()

    window = tk.Tk()
    window.title("題目顯示")
    window.geometry("600x600")
    window.attributes("-topmost", True)

    current_mode = "light"
    bg_color = "white"
    fg_color = "black"

    mode_button = tk.Button(window, text="切換模式", command=toggle_mode, fg=fg_color, bg=bg_color)
    mode_button.pack(side=tk.TOP, anchor=tk.NE, padx=10, pady=10)

    checked_data = load_checked_data()
    total_questions = len(question_data)
    current_question_index = get_last_index(checked_data, question_data)

    display_question(question_data, current_question_index, total_questions, checked_data)
    window.mainloop()
