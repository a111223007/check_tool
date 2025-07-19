import json

def clean_questions(filename, target_schools, output_file=None):
    # 讀取原始 JSON 檔案
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cleaned_data = []
    removed_school_count = 0
    for item in data:
        school = item.get("question_data", {}).get("school", "")
        if school in target_schools:
            removed_school_count += 1
            continue  # 跳過要刪除的學校

        # 移除 total_question_number 欄位
        item.pop("total_question_number", None)
        item.pop("status", None)
        cleaned_data.append(item)

    # 寫回檔案
    output_filename = output_file if output_file else filename
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

    print(f"已刪除 {removed_school_count} 筆指定學校題目，並移除 total_question_number 欄位，結果儲存於：{output_filename}")


# 使用範例
clean_questions(
    filename='check_exam_output.json',
    target_schools=['私立健行科技大學','私立靜宜大學', '私立元智大學','私立元培醫事科技大學','私立南臺科技大學'],
    output_file='filtered_check_exam_output.json'  # 可省略以覆蓋原檔
)
