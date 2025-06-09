import json
import tkinter as tk
from tkinter import messagebox, scrolledtext

def load_error_data(filename="error_exam_output.json"):
    """載入錯誤題目資料"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        messagebox.showerror("錯誤", f"找不到 '{filename}' 檔案。請確認檔案是否存在。")
        return []
    except json.JSONDecodeError:
        messagebox.showwarning("警告", f"'{filename}' 檔案格式不正確或為空。")
        return []

def save_error_data(data, filename="error_exam_output.json"):
    """保存錯誤題目資料"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("保存成功", "錯誤題目資料已成功保存。")
        return True
    except Exception as e:
        messagebox.showerror("保存失敗", f"保存檔案時發生錯誤: {e}")
        return False

class ErrorEditorApp:
    def __init__(self, master):
        self.master = master
        master.title("錯誤題目編輯器")
        master.geometry("800x700")
        master.attributes("-topmost", True)

        self.error_data = load_error_data()
        self.current_index = 0
        self.total_errors = len(self.error_data)

        # 建立一個 total_question_number 到列表索引的映射，用於快速查找
        self.total_q_num_map = {
            item.get("total_question_number"): i
            for i, item in enumerate(self.error_data)
        }

        if not self.error_data:
            messagebox.showinfo("無錯誤資料", "目前沒有錯誤題目需要編輯。")
            master.destroy()
            return

        self.create_widgets()
        self.display_current_error()

    def create_widgets(self):
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)

        # Canvas for scrolling
        self.canvas = tk.Canvas(self.master, bg="white")
        self.scrollbar = tk.Scrollbar(self.master, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- 搜尋功能區 ---
        self.search_frame = tk.LabelFrame(self.scrollable_frame, text="搜尋題目", padx=10, pady=5, bg="white")
        self.search_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(self.search_frame, text="輸入總問題編號:", bg="white").pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(self.search_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_button = tk.Button(self.search_frame, text="搜尋", command=self.search_question, bg="lightyellow")
        self.search_button.pack(side=tk.LEFT, padx=5)


        # --- 編輯區域 ---
        self.editor_frame = tk.LabelFrame(self.scrollable_frame, text="編輯題目資訊", padx=10, pady=10, bg="white")
        self.editor_frame.pack(pady=10, padx=10, fill="x")

        # 顯示題目索引
        self.index_label = tk.Label(self.editor_frame, text="", bg="white")
        self.index_label.grid(row=0, column=0, columnspan=2, pady=5)

        # 學校 (標籤)
        tk.Label(self.editor_frame, text="學校:", bg="white").grid(row=1, column=0, sticky="w", pady=2)
        self.school_label_val = tk.Label(self.editor_frame, text="", bg="white", anchor="w")
        self.school_label_val.grid(row=1, column=1, sticky="ew", pady=2)

        # 科系 (標籤)
        tk.Label(self.editor_frame, text="科系:", bg="white").grid(row=2, column=0, sticky="w", pady=2)
        self.department_label_val = tk.Label(self.editor_frame, text="", bg="white", anchor="w")
        self.department_label_val.grid(row=2, column=1, sticky="ew", pady=2)

        # 年份 (標籤)
        tk.Label(self.editor_frame, text="年份:", bg="white").grid(row=3, column=0, sticky="w", pady=2)
        self.year_label_val = tk.Label(self.editor_frame, text="", bg="white", anchor="w")
        self.year_label_val.grid(row=3, column=1, sticky="ew", pady=2)

        # 題號 (可修改)
        tk.Label(self.editor_frame, text="題號:", bg="white").grid(row=4, column=0, sticky="w", pady=2)
        self.question_number_entry = tk.Entry(self.editor_frame, width=50)
        self.question_number_entry.grid(row=4, column=1, sticky="ew", pady=2)

        # 題目文字 (可修改)
        tk.Label(self.editor_frame, text="題目文字:", bg="white").grid(row=5, column=0, sticky="nw", pady=2)
        self.question_text_text = scrolledtext.ScrolledText(self.editor_frame, width=60, height=8, wrap=tk.WORD)
        self.question_text_text.grid(row=5, column=1, sticky="ew", pady=2)

        # 選項 (可修改，多行)
        tk.Label(self.editor_frame, text="選項 (每行一個):", bg="white").grid(row=6, column=0, sticky="nw", pady=2)
        self.options_text = scrolledtext.ScrolledText(self.editor_frame, width=60, height=5, wrap=tk.WORD)
        self.options_text.grid(row=6, column=1, sticky="ew", pady=2)

        # 圖片路徑 (可修改，多行，如果有多個)
        tk.Label(self.editor_frame, text="圖片路徑 (每行一個):", bg="white").grid(row=7, column=0, sticky="nw", pady=2)
        self.image_file_text = scrolledtext.ScrolledText(self.editor_frame, width=60, height=3, wrap=tk.WORD)
        self.image_file_text.grid(row=7, column=1, sticky="ew", pady=2)

        # 狀態 (顯示，不可修改)
        tk.Label(self.editor_frame, text="當前錯誤狀態:", bg="white").grid(row=8, column=0, sticky="w", pady=2)
        self.status_label = tk.Label(self.editor_frame, text="", fg="red", bg="white")
        self.status_label.grid(row=8, column=1, sticky="w", pady=2)

        # 按鈕區
        button_frame = tk.Frame(self.scrollable_frame, bg="white")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="上一題", command=self.prev_error, bg="lightgray", fg="black").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="保存並下一題", command=self.save_and_next, bg="lightblue", fg="black").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="保存所有修改", command=self.save_all, bg="lightgreen", fg="black").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="刪除此錯誤", command=self.delete_current_error, fg="red", bg="salmon").pack(side=tk.LEFT, padx=5)


    def display_current_error(self):
        if not self.error_data:
            messagebox.showinfo("完成", "所有錯誤題目已編輯完畢或已刪除。")
            self.master.destroy()
            return

        # 確保索引在有效範圍內
        if self.current_index >= len(self.error_data):
            self.current_index = len(self.error_data) - 1
        if self.current_index < 0:
            self.current_index = 0

        question = self.error_data[self.current_index]
        q_data = question.get("question_data", {})
        status = question.get("status", [])

        self.index_label.config(text=f"第 {self.current_index + 1} / {self.total_errors} 題 (總問題編號: {question.get('total_question_number', 'N/A')})")

        # 更新學校、科系、年份標籤
        self.school_label_val.config(text=q_data.get("school", ""))
        self.department_label_val.config(text=q_data.get("department", ""))
        self.year_label_val.config(text=q_data.get("year", ""))

        self.question_number_entry.delete(0, tk.END)
        self.question_number_entry.insert(0, q_data.get("question_number", ""))

        self.question_text_text.delete(1.0, tk.END)
        self.question_text_text.insert(1.0, q_data.get("question_text", ""))

        self.options_text.delete(1.0, tk.END)
        if q_data.get("options"):
            self.options_text.insert(1.0, "\n".join(q_data["options"]))
        else:
            self.options_text.delete(1.0, tk.END) # 清空，如果沒有選項

        self.image_file_text.delete(1.0, tk.END)
        if q_data.get("image_file"):
            self.image_file_text.insert(1.0, "\n".join(q_data["image_file"]))
        else:
            self.image_file_text.delete(1.0, tk.END) # 清空，如果沒有圖片

        self.status_label.config(text="、".join(status))

    def update_current_error_data(self):
        """從 GUI 欄位讀取修改後的數據並更新到 self.error_data"""
        if not self.error_data:
            return False

        current_item = self.error_data[self.current_index]
        q_data = current_item.get("question_data", {})

        # 學校、科系、年份不再從 Entry 獲取，保持原值
        # q_data["school"] = self.school_label_val.cget("text") # 這樣做會將其從 Entry 的值替換為 Label 的值
        # q_data["department"] = self.department_label_val.cget("text")
        # q_data["year"] = self.year_label_val.cget("text")

        q_data["question_number"] = self.question_number_entry.get()
        q_data["question_text"] = self.question_text_text.get(1.0, tk.END).strip()
        q_data["options"] = [opt.strip() for opt in self.options_text.get(1.0, tk.END).strip().split('\n') if opt.strip()]
        q_data["image_file"] = [img.strip() for img in self.image_file_text.get(1.0, tk.END).strip().split('\n') if img.strip()]

        current_item["question_data"] = q_data # 確保更新回原字典
        return True

    def search_question(self):
        """根據輸入的 total_question_number 搜尋並跳轉到對應題目"""
        search_value = self.search_entry.get().strip()
        if not search_value:
            messagebox.showwarning("警告", "請輸入總問題編號。")
            return

        try:
            target_q_num = int(search_value)
        except ValueError:
            messagebox.showerror("錯誤", "總問題編號必須是數字。")
            return

        # 檢查當前題目是否有未保存的修改
        self.update_current_error_data() # 保存當前題目的修改

        # 使用之前建立的 total_q_num_map 進行快速查找
        if target_q_num in self.total_q_num_map:
            target_index = self.total_q_num_map[target_q_num]
            self.current_index = target_index
            self.display_current_error()
        else:
            messagebox.showinfo("未找到", f"找不到總問題編號為 '{target_q_num}' 的錯誤題目。")

    def save_and_next(self):
        if self.update_current_error_data():
            # 這裡不直接保存到檔案，而是等待用戶點擊「保存所有修改」
            self.current_index += 1
            if self.current_index < self.total_errors:
                self.display_current_error()
            else:
                messagebox.showinfo("完成", "已到達最後一題。請點擊 '保存所有修改' 以保存您的工作。")
                # 重新設定索引以便可以回頭看
                self.current_index = self.total_errors - 1
                self.display_current_error()


    def prev_error(self):
        if self.current_index > 0:
            # 確保先保存當前修改 (如果有的話)
            self.update_current_error_data()
            self.current_index -= 1
            self.display_current_error()
        else:
            messagebox.showinfo("提示", "已經是第一題了。")

    def save_all(self):
        # 確保最後一題的修改也被保存
        if self.error_data:
            self.update_current_error_data()
        
        if save_error_data(self.error_data):
            messagebox.showinfo("保存成功", "所有修改已保存到 error_exam_output.json。")
            # 重新載入以更新 total_errors 和 total_q_num_map，因為可能刪除了
            self.error_data = load_error_data()
            self.total_errors = len(self.error_data)
            self.total_q_num_map = {
                item.get("total_question_number"): i
                for i, item in enumerate(self.error_data)
            }
            if self.total_errors == 0:
                messagebox.showinfo("無錯誤資料", "目前沒有錯誤題目需要編輯。")
                self.master.destroy()
            else:
                # 確保 current_index 不會超出範圍
                if self.current_index >= self.total_errors:
                    self.current_index = self.total_errors - 1
                self.display_current_error() # 重新顯示當前題目，更新索引顯示


    def delete_current_error(self):
        if messagebox.askyesno("確認刪除", "你確定要刪除當前這個錯誤題目嗎？此操作不可逆！"):
            if self.error_data:
                deleted_q_num = self.error_data[self.current_index].get("total_question_number")
                del self.error_data[self.current_index]
                self.total_errors = len(self.error_data)

                # 更新 map
                del self.total_q_num_map[deleted_q_num] # 從 map 中移除被刪除的
                # 因為刪除導致索引變化，需要重建 map
                self.total_q_num_map = {
                    item.get("total_question_number"): i
                    for i, item in enumerate(self.error_data)
                }

                if self.total_errors == 0:
                    messagebox.showinfo("完成", "所有錯誤題目已刪除。")
                    save_error_data(self.error_data) # 保存空列表
                    self.master.destroy()
                else:
                    # 如果刪除的是最後一個，索引往前移
                    if self.current_index >= self.total_errors:
                        self.current_index = self.total_errors - 1
                    messagebox.showinfo("已刪除", "當前題目已從列表中刪除。")
                    self.display_current_error()
                    save_error_data(self.error_data) # 每次刪除後即時保存

if __name__ == "__main__":
    root = tk.Tk()
    app = ErrorEditorApp(root)
    root.mainloop()