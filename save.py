import json
import sys
import os

def save_to_json(status_list, question, question_index):
    save_data = {
        "total_question_number": question_index + 1,
        "status": status_list,
        "question_data": question
    }

    filename = "check_exam_output.json"
    data = []

    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

    found = False
    for item in data:
        if item.get('question_data') == question:
            item['status'] = status_list  # 更新為新狀態
            item['total_question_number'] = question_index + 1  # 確保編號也同步更新
            found = True
            break

    if not found:
        data.append(save_data)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("用法：python save.py <status_json> <question_json> <question_index>")
    else:
        status_json = sys.argv[1]
        question_json = sys.argv[2]
        question_index = int(sys.argv[3])

        try:
            status_list = json.loads(status_json)
            question = json.loads(question_json)

            if not isinstance(status_list, list):
                status_list = [status_list]  # 保險：即使傳入單一字串也能處理

            save_to_json(status_list, question, question_index)
        except json.JSONDecodeError:
            print("錯誤：無效的 JSON 資料。")