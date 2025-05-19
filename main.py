import json
import tkinter as tk
from tkinter import messagebox
import subprocess
from PIL import Image, ImageTk  # 處理圖片 (需安裝 Pillow: pip install Pillow)

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

def display_question(question_data, question_index, total_questions, checked_data):
    question = question_data[question_index]
    # 清空除了 mode_button 之外的視窗內容
    for widget in window.winfo_children():
        if widget != mode_button:
            widget.destroy()

    apply_colors()

    info_frame = tk.Frame(window, bg=bg_color)
    info_frame.pack(pady=10)
    tk.Label(info_frame, text=f"學校: {question['school']}", fg=fg_color, bg=bg_color).pack()
    tk.Label(info_frame, text=f"科系: {question['department']}", fg=fg_color, bg=bg_color).pack()
    tk.Label(info_frame, text=f"年份: {question['year']}", fg=fg_color, bg=bg_color).pack()

    # 顯示題號和總題數
    tk.Label(info_frame, text=f"題號: {question['question_number']} ({question_index + 1}/{total_questions})", fg=fg_color, bg=bg_color).pack()

    # 顯示題目文字
    question_label = tk.Label(window, text="題目: " + question['question_text'], fg=fg_color, bg=bg_color, wraplength=500)
    question_label.pack(pady=10)

    # 顯示圖片路徑 (如果有的話)
    if question['image_file']:
        image_filename = question['image_file'][0]
        tk.Label(window, text=f"圖片路徑 : {image_filename}", fg=fg_color, bg=bg_color).pack(pady=10)
    else:
        tk.Label(window, text="圖片 : 沒有圖片", fg=fg_color, bg=bg_color).pack(pady=10)

    # 顯示已儲存的狀態 (如果有的話)
    saved_status = get_saved_status(checked_data, question['question_number'])
    if saved_status == "確認":
        tk.Label(window, text=f"狀態: {saved_status}", fg="green", bg=bg_color).pack(pady=5)
    elif saved_status == "錯誤":
        tk.Label(window, text=f"狀態: {saved_status}", fg="red", bg=bg_color).pack(pady=5)
    else:
        tk.Label(window, text="狀態: 未標記", fg="orange", bg=bg_color).pack(pady=5)

    button_frame = tk.Frame(window, bg=bg_color)
    button_frame.pack(pady=10)

    def correct_answer():
        save_result("確認", question)
        next_question()

    def incorrect_answer():
        save_result("錯誤", question)
        next_question()

    def previous_question():
        global current_question_index
        if current_question_index > 0:
            current_question_index -= 1
            checked_data = load_checked_data()  # 重新讀取資料
            display_question(question_data, current_question_index, total_questions, checked_data)

    def next_question():
        global current_question_index
        current_question_index += 1
        if current_question_index < len(question_data):
            checked_data = load_checked_data()  # 重新讀取資料
            display_question(question_data, current_question_index, total_questions, checked_data)
        else:
            messagebox.showinfo("結束", "所有題目已完成。", bg=bg_color, fg=fg_color)
            window.destroy()

    tk.Button(button_frame, text="正確", command=correct_answer, fg="black", bg="white").pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="錯誤", command=incorrect_answer, fg="black", bg="white").pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="上一題", command=previous_question, fg="black", bg="white").pack(side=tk.LEFT, padx=10)


def get_saved_status(checked_data, question_number):
    for item in checked_data:
        if item['question_number'] == question_number:
            return item['status']
    return None

def save_result(status, question):
    # 將題目資料轉換為 JSON 字串，並傳遞給 save.py
    question_json = json.dumps(question, ensure_ascii=False)  # 處理中文
    try:
        subprocess.run(
            ["python", "save.py", status, question_json],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"執行 save.py 時發生錯誤: {e.stderr}")
    except FileNotFoundError:
        print("錯誤：找不到 save.py 檔案。")

def toggle_mode():
    global current_mode, bg_color, fg_color, total_questions  # 確保 total_questions 在這裡可見
    if current_mode == "light":
        current_mode = "dark"
        bg_color = "black"
        fg_color = "white"
    else:
        current_mode = "light"
        bg_color = "white"
        fg_color = "black"
    apply_colors()
    checked_data = load_checked_data()  # 重新讀取資料
    display_question(question_data, current_question_index, total_questions, checked_data)

def apply_colors():
    window.config(bg=bg_color)
    if mode_button:
        mode_button.config(fg=fg_color, bg=bg_color)

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
    window.geometry("600x450")

    current_mode = "light"
    bg_color = "white"
    fg_color = "black"

    mode_button = tk.Button(window, text="切換模式", command=toggle_mode, fg=fg_color, bg=bg_color)
    mode_button.pack(side=tk.TOP, anchor=tk.NE, padx=10, pady=10)

    # 讀取 check_exam_output.json
    checked_data = load_checked_data()

    # 取得總題數
    total_questions = len(question_data)

    current_question_index = 0
    display_question(question_data, current_question_index, total_questions, checked_data)

    window.mainloop()