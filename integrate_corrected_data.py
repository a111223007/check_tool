import json

def integrate_corrected_errors(input_filename="check_exam_output.json", error_filename="error_exam_output.json", output_filename="check_exam_output.json"):
    
    original_data = []
    error_data = {}
    
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        print(f"已從 '{input_filename}' 載入 {len(original_data)} 筆資料。")
    except FileNotFoundError:
        print(f"錯誤：找不到原始輸入檔案 '{input_filename}'。無法繼續。")
        return
    except json.JSONDecodeError:
        print(f"錯誤：原始輸入檔案 '{input_filename}' 的 JSON 格式不正確。無法繼續。")
        return

    try:
        with open(error_filename, 'r', encoding='utf-8') as f:
            errors_list = json.load(f)
            error_data = {item.get("total_question_number"): item for item in errors_list}
        print(f"已從 '{error_filename}' 載入 {len(errors_list)} 筆錯誤資料。")
    except FileNotFoundError:
        print(f"警告：找不到錯誤檔案 '{error_filename}'。沒有錯誤可以整合。'{input_filename}' 將保持不變。")
        return
    except json.JSONDecodeError:
        print(f"錯誤：錯誤檔案 '{error_filename}' 的 JSON 格式不正確。無法整合錯誤。")
        return

    updated_data = []

    processed_q_numbers = set()

    for item in original_data:
        total_q_num = item.get("total_question_number")
        
        if total_q_num in error_data:
            error_version = error_data[total_q_num]
            status_list_error_version = error_version.get("status", [])

            if all(s == "確認" for s in status_list_error_version):
                updated_data.append(error_version)
            else:
                updated_data.append(error_version)
            processed_q_numbers.add(total_q_num)
        else:
            updated_data.append(item)
            processed_q_numbers.add(total_q_num)
            
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)
        print(f"已成功將 '{output_filename}' 更新，共 {len(updated_data)} 筆資料。")
    except Exception as e:
        print(f"儲存更新資料到 '{output_filename}' 時發生錯誤：{e}")

if __name__ == "__main__":
    integrate_corrected_errors()