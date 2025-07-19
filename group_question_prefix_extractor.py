import json
import re

GROUP_END_PUNCTUATION = (":", "：", "?", "？", "。",  "." , ";", "；")

def find_common_prefix(texts):
    """找出多行文字的共同前綴(以標點為界)"""
    # 找出所有子題第一段前綴（到第一個標點為止）
    prefixes = []
    for t in texts:
        for p in GROUP_END_PUNCTUATION:
            if p in t:
                idx = t.index(p) + 1
                prefixes.append(t[:idx])
                break
        else:
            # 沒有標點則整句當前綴
            prefixes.append(t)

    if not prefixes:
        return ""

    # 找出所有前綴的最短長度
    min_len = min(len(p) for p in prefixes)
    # 逐字比對，找最大共同前綴
    common_prefix = ""
    for i in range(min_len):
        c = prefixes[0][i]
        if all(p[i] == c for p in prefixes):
            common_prefix += c
        else:
            break

    # 如果最後字元不是標點符號，嘗試往前回退到標點符號
    while common_prefix and common_prefix[-1] not in GROUP_END_PUNCTUATION:
        common_prefix = common_prefix[:-1]

    return common_prefix.strip()

def process_group(group):
    if group["type"] != "group" or group.get("group_question_text"):
        # 非空group_question_text不處理
        return group

    sub_questions = group.get("sub_questions", [])
    if not sub_questions:
        return group

    # 取所有子題 question_text 第一行（或全部？先取第一行）
    first_lines = []
    for sq in sub_questions:
        # 只取第一行（遇到換行符號切割）
        first_line = sq["question_text"].splitlines()[0].strip()
        first_lines.append(first_line)

    # 找出共同前綴
    common_prefix = find_common_prefix(first_lines)
    if not common_prefix:
        return group  # 找不到共同前綴不動

    # 將共同前綴放入 group_question_text，子題 question_text 裡去除該前綴
    for sq in sub_questions:
        text = sq["question_text"]
        if text.startswith(common_prefix):
            sq["question_text"] = text[len(common_prefix):]
        else:
            # 若開頭不完全相同，但可能有換行或空白，嘗試更寬鬆地去除
            sq["question_text"] = re.sub(r"^\s*" + re.escape(common_prefix), "", text)

    group["group_question_text"] = common_prefix
    return group

def main():
    with open("grouped_exam.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    new_data = []
    for group in data:
        if group.get("type") == "group" and group.get("group_question_text") == "":
            new_group = process_group(group)
            new_data.append(new_group)
        else:
            new_data.append(group)

    with open("grouped_exam_processed.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
