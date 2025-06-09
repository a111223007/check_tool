# process_exam_data.py (請將此程式碼整合到你的實際處理邏輯中)
import json

def process_and_update_error_data(input_filename="check_exam_output.json", output_error_filename="error_exam_output.json"):
    """
    處理原始檢查結果，篩選錯誤資料，並智能更新 error_exam_output.json。
    智能更新規則：如果現有錯誤日誌中的題目已被用戶修改，則以日誌中的為準。
    """
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

    # 建立現有錯誤的唯一識別符集合，用於快速查找
    # 這裡使用 'total_question_number' 作為主要識別，因為它是題目在原始檔案中的索引。
    # 這裡的 key 應該是 total_question_number
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

                    # 比較 question_data 的核心部分是否相同
                    # 注意：這裡的比較應該基於原始解析時的數據，
                    # 如果用戶在 edit_errors.py 中修改了這些數據，
                    # 我們就以用戶修改過的為準，不再從 input_filename 中新增。

                    # 最簡單的判斷方式：如果 total_question_number 相同，
                    # 並且 existing_item 的 status 不再是 "確認" (因為用戶編輯器只處理錯誤)，
                    # 那麼我們就假設這個條目已經被處理過或正在處理中，以 existing_item 為準。
                    # 如果 input_filename 裡的 status 變成 "確認"了，那它就不應該在這裡了。

                    # 更精確的判斷，如果 'question_data' 在兩者之間完全相同，那麼它就是重複的。
                    # 如果不同，則表示用戶已經在編輯器中修改過，我們就保留用戶修改的。
                    input_question_data_str = json.dumps(item.get("question_data", {}), sort_keys=True, ensure_ascii=False)
                    existing_question_data_str = json.dumps(existing_item.get("question_data", {}), sort_keys=True, ensure_ascii=False)

                    if input_question_data_str != existing_question_data_str:
                        # 核心內容不同，表示用戶已修改或原始數據發生變化
                        # 我們選擇保留 existing_item（用戶修改過的），不加入新的
                        print(f"第 {current_total_q_num} 號錯誤題目在 '{output_error_filename}' 中有更新，保留現有版本。")
                        new_errors_from_input.append(existing_item) # 將現有已修改的也加回來，以重新寫入完整檔案
                    else:
                        # 核心內容相同，表示是重複的未修改錯誤，無需新增
                        new_errors_from_input.append(existing_item) # 還是需要把這個舊的錯誤加回來
                else:
                    # 這是新的錯誤，直接添加
                    new_errors_from_input.append(item)
                    print(f"新增新的錯誤題目：{current_total_q_num}")
            else:
                # 如果這條目在新的 input 中是「確認」狀態，但它存在於舊的錯誤日誌中
                # 說明這個題目已經被修正了，應該從錯誤日誌中移除
                if current_total_q_num in existing_error_map:
                    print(f"第 {current_total_q_num} 號題目在 '{input_filename}' 中已修正為 '確認'，將從錯誤日誌中移除。")
                    # 不將其添加到 new_errors_from_input，這樣它就不會被寫回錯誤日誌了

        # 3. 寫回更新後的錯誤日誌
        # 這裡需要一個過濾機制，確保 `new_errors_from_input` 不包含被移除的項目
        # 最簡單的方法是重新構建一個列表，只包含需要保留的錯誤
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
            # else: 如果是「確認」，則不添加到錯誤日誌

        # 還要確保那些只存在於 old_error_log 但不在 current_input_data 裡的錯誤也被保留 (如果它們沒被修正的話)
        # 例如，一個題目在 input_filename 中被移除了，但它曾經是一個錯誤，並且被用戶修改過。
        # 為了簡化，我們主要關注 input_filename 中的錯誤，並優先處理 existing_error_map 中的修改。

        # 最終寫入的列表應該是 `existing_error_log` 裡面的，如果它們在 `input_filename` 中仍然是錯誤，
        # 並且 `input_filename` 中新發現的錯誤。
        
        # 更好的策略：
        # 遍歷原始輸入資料
        #   如果它是錯誤：
        #       檢查它是否在 existing_error_map 中
        #           如果在：使用 existing_error_map 中的版本
        #           如果不在：使用 input_filename 中的版本
        #   如果它是正確的 (status 是 "確認")：
        #       如果它在 existing_error_map 中：從 existing_error_map 中移除它 (表示已被修正)
        
        # 重新構建最終列表
        temp_merged_errors = {}

        # 將現有錯誤日誌中的項目先放入字典，以便優先處理用戶修改
        for item in existing_error_log:
            temp_merged_errors[item.get("total_question_number")] = item

        # 遍歷新的輸入資料
        for item in current_input_data:
            total_q_num = item.get("total_question_number")
            status_list = item.get("status", [])

            if any(s != "確認" for s in status_list): # 如果 input 中的是錯誤
                if total_q_num not in temp_merged_errors:
                    # 新的錯誤，加入
                    temp_merged_errors[total_q_num] = item
                # else: 如果已存在，則 `temp_merged_errors` 中已是用戶修改過的版本，保持不變
            else: # 如果 input 中的是正確
                if total_q_num in temp_merged_errors:
                    # 該題目已修正，從錯誤日誌中移除
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

# 範例執行 (在你的 process_exam_data.py 中呼叫此函式)
if __name__ == "__main__":
    # 假設你的 check_exam_output.json 已經包含經過 main.py 標記的資料
    # 然後你會執行 process_and_update_error_data 來更新 error_exam_output.json
    process_and_update_error_data()