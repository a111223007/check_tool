# save.py
import json
import sys

def save_to_check_exam_output(status_list, question_item_to_save):
    """
    更新或新增題目到 check_exam_output.json 檔案。
    根據 total_question_number 來匹配並更新。
    """
    filename = 'check_exam_output.json'
    data = []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: '{filename}' not found. Creating a new one.", file=sys.stderr)
    except json.JSONDecodeError:
        print(f"Warning: '{filename}' is empty or malformed. Starting with empty data.", file=sys.stderr)
        data = [] # 如果檔案損壞，則從空列表開始

    updated = False
    target_total_q_num = question_item_to_save.get('total_question_number')

    if target_total_q_num is None:
        print("Error: 'total_question_number' missing in question_item. Cannot save.", file=sys.stderr)
        return

    # 尋找並更新現有題目
    for i, item in enumerate(data):
        if item.get('total_question_number') == target_total_q_num:
            # 更新狀態
            data[i]['status'] = status_list
            # 更新 question_data
            data[i]['question_data'] = question_item_to_save['question_data']
            updated = True
            print(f"Updated question {target_total_q_num} in '{filename}'.")
            break
    
    # 如果是新題目，則新增
    if not updated:
        # 確保 total_question_number 在儲存時是正確的
        # 這裡我們假設傳入的 question_item_to_save 已經是一個完整的 item，
        # 包含 'total_question_number' 和 'question_data'。
        # save_result 傳入的是整個 question_item，所以不需要重新構建
        new_item = {
            "total_question_number": target_total_q_num,
            "status": status_list,
            "question_data": question_item_to_save['question_data']
        }
        data.append(new_item)
        # 為了保持 total_question_number 的順序，可以考慮排序
        data.sort(key=lambda x: x.get('total_question_number', float('inf')))
        print(f"Added new question {target_total_q_num} to '{filename}'.")

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved to '{filename}'.")
    except Exception as e:
        print(f"Error saving to '{filename}': {e}", file=sys.stderr)

if __name__ == "__main__":
    # 從命令列參數獲取狀態列表和題目資料
    if len(sys.argv) < 3:
        print("Usage: python save.py <status_json> <question_data_json>", file=sys.stderr)
        sys.exit(1)

    try:
        # sys.argv[1] 是 status 的 JSON 字串
        status_from_arg = json.loads(sys.argv[1])
        # sys.argv[2] 是 question_item (包含 total_question_number, status, question_data) 的 JSON 字串
        question_item_from_arg = json.loads(sys.argv[2])
        
        save_to_check_exam_output(status_from_arg, question_item_from_arg)

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON argument: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)