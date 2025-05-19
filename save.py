import json
import sys
import os

def save_to_json(status, question):
    """
    將標記結果儲存到 check_exam_output.json 檔案。
    更新現有題目的狀態，如果存在的話。

    Args:
        status: "確認" 或 "錯誤"。
        question: 題目資料 (字典)。
    """

    # 確保 question_number 是字串
    if 'question_number' in question:
        question['question_number'] = str(question['question_number'])

    save_data = {
        "question_number": question.get('question_number', 'N/A'),
        "status": status,
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

    # 檢查是否已存在相同題號的紀錄
    found = False
    for item in data:
        if item['question_number'] == save_data['question_number']:
            item['status'] = status
            item['question_data'] = question
            found = True
            break

    # 如果不存在，則新增紀錄
    if not found:
        data.append(save_data)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法：python save.py <status> <question_json>")
    else:
        status = sys.argv[1]
        question_json = sys.argv[2]
        try:
            question = json.loads(question_json)
            save_to_json(status, question)
        except json.JSONDecodeError:
            print("錯誤：無效的 JSON 資料。")