# process_exam_data.py (請將此程式碼整合到你的實際處理邏輯中)
import json

def process_and_update_error_data(input_filename="check_exam_output.json", output_error_filename="error_exam_output.json"):

    new_errors_from_input = []
    
    # 1. 載入當前的錯誤日誌 (用戶可能已編輯過的版本)
    existing_error_log = []
    try:
        with open(output_error_filename, 'r', encoding='utf-8') as f:
            existing_error_log = json.load(f)
        print(f"已載入 {len(existing_error_log)} 筆現有錯誤日誌。")
    except FileNotFoundError:
        print(f"找不到 '{output_error_filename}'，將創建新檔案。")
    except json.JSONDecodeError:
        print(f"'{output_error_filename}' 格式錯誤或為空，將重新建立。")
        existing_error_log = []

    existing_error_map = {item.get("total_question_number"): item for item in existing_error_log}

    # 2. 處理新的輸入數據
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            current_input_data = json.load(f)

        for item in current_input_data:
            current_total_q_num = item.get("total_question_number")
            status_list = item.get("status", [])

            # 如果 status 包含非「確認」狀態
            if any(s != "確認" for s in status_list):
                # 檢查這個錯誤是否已經在現有的錯誤日誌中
                if current_total_q_num in existing_error_map:
                    # 獲取現有日誌中的對應項目
                    existing_item = existing_error_map[current_total_q_num]
                    input_question_data_str = json.dumps(item.get("question_data", {}), sort_keys=True, ensure_ascii=False)
                    existing_question_data_str = json.dumps(existing_item.get("question_data", {}), sort_keys=True, ensure_ascii=False)

                    if input_question_data_str != existing_question_data_str:
                        print(f"第 {current_total_q_num} 號錯誤題目在 '{output_error_filename}' 中有更新，保留現有版本。")
                        new_errors_from_input.append(existing_item) # 將現有已修改的也加回來，以重新寫入完整檔案
                    else:
                        new_errors_from_input.append(existing_item) # 還是需要把這個舊的錯誤加回來
                else:
                    new_errors_from_input.append(item)
                    print(f"新增新的錯誤題目：{current_total_q_num}")
            else:
                if current_total_q_num in existing_error_map:
                    print(f"第 {current_total_q_num} 號題目在 '{input_filename}' 中已修正為 '確認'，將從錯誤日誌中移除。")

        final_errors_to_save = []
        processed_total_q_numbers = set()

        for item in current_input_data:
            current_total_q_num = item.get("total_question_number")
            status_list = item.get("status", [])

            if any(s != "確認" for s in status_list): # 原始 input 中是錯誤
                if current_total_q_num in existing_error_map:
                    # 以 existing_error_map 中的版本為準 (用戶修改過的)
                    if current_total_q_num not in processed_total_q_numbers: # 避免重複添加
                        final_errors_to_save.append(existing_error_map[current_total_q_num])
                        processed_total_q_numbers.add(current_total_q_num)
                else:
                    # 新的錯誤
                    if current_total_q_num not in processed_total_q_numbers:
                        final_errors_to_save.append(item)
                        processed_total_q_numbers.add(current_total_q_num)

        temp_merged_errors = {}

        for item in existing_error_log:
            temp_merged_errors[item.get("total_question_number")] = item

        for item in current_input_data:
            total_q_num = item.get("total_question_number")
            status_list = item.get("status", [])

            if any(s != "確認" for s in status_list): # 如果 input 中的是錯誤
                if total_q_num not in temp_merged_errors:
                    temp_merged_errors[total_q_num] = item
            else: 
                if total_q_num in temp_merged_errors:
                    del temp_merged_errors[total_q_num]
        
        final_errors_to_save = list(temp_merged_errors.values())

        with open(output_error_filename, 'w', encoding='utf-8') as f:
            json.dump(final_errors_to_save, f, ensure_ascii=False, indent=4)
        print(f"錯誤日誌 '{output_error_filename}' 已更新。總共 {len(final_errors_to_save)} 筆錯誤資料。")

    except FileNotFoundError:
        print(f"錯誤：找不到原始輸入檔案 '{input_filename}'。")
    except json.JSONDecodeError:
        print(f"錯誤：原始輸入檔案 '{input_filename}' 格式不正確。")
    except Exception as e:
        print(f"發生未知錯誤：{e}")

if __name__ == "__main__":
    process_and_update_error_data()