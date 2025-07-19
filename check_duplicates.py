import json
import re
from collections import defaultdict
from copy import deepcopy

# -------- 可調參數 --------
INPUT_FILE = "check_exam_output.json"
OUTPUT_FILE = "grouped_exam.json"
MIN_PREFIX_LEN = 30
TRIM_WHITESPACE = True
KEEP_EMPTY_SUBTEXT = False

GROUP_END_PUNCTUATION = (":", "：", "?", "？", "。",  "." , ";", "；")


# -------- 工具函數 --------
def _norm(s: str) -> str:
    if s is None:
        return ""
    return s.strip() if TRIM_WHITESPACE else s


def longest_common_prefix(texts, min_prefix_len=MIN_PREFIX_LEN) -> str:
    if not texts:
        return ""
    prefix = texts[0]
    for t in texts[1:]:
        i = 0
        while i < len(prefix) and i < len(t) and prefix[i] == t[i]:
            i += 1
        prefix = prefix[:i]
        if not prefix:
            break
    prefix = prefix.strip()
    return prefix if len(prefix) >= min_prefix_len else ""


def is_valid_group_prefix(prefix: str) -> bool:
    return prefix and prefix[-1] in GROUP_END_PUNCTUATION


def are_consecutive_numbers(nums: list) -> bool:
    nums = sorted(nums)
    return all(b - a == 1 for a, b in zip(nums, nums[1:]))


def collapse_meta(items, field):
    vals = []
    for it in items:
        qd = it.get("question_data", {})
        vals.append(qd.get(field))
    uniq = {v for v in vals if v is not None}
    return uniq.pop() if len(uniq) == 1 else None


def collapse_meta_from_flat(items, field):
    vals = {it[field] for it in items if it[field] is not None}
    return vals.pop() if len(vals) == 1 else None


def normalize_input(raw_list):
    normed = []
    for obj in raw_list:
        qd = obj.get("question_data", obj)
        if "group_question_text" in qd and "sub_questions" in qd:
            group_text = _norm(qd["group_question_text"])
            for sub in qd["sub_questions"]:
                sub_copy = deepcopy(obj)
                new_qd = {
                    "school": qd.get("school"),
                    "department": qd.get("department"),
                    "year": qd.get("year"),
                    "question_number": sub.get("question_number"),
                    "question_text": f"{group_text}\n\n{sub.get('question_text', '')}",
                    "options": sub.get("options", []),
                    "type": sub.get("type"),
                    "image_file": sub.get("image_file", []),
                }
                sub_copy["question_data"] = new_qd
                normed.append(sub_copy)
        else:
            normed.append(obj)
    return normed


def flatten_for_group(obj):
    qd = obj.get("question_data", {})
    return {
        "source": obj,
        "status": obj.get("status", []),
        "school": qd.get("school"),
        "department": qd.get("department"),
        "year": qd.get("year"),
        "question_number": qd.get("question_number"),
        "question_text": _norm(qd.get("question_text", "")),
        "options": qd.get("options", []),
        "answer": qd.get("answer"),
        "question_type": qd.get("type"),
        "image_file": qd.get("image_file", []),
    }


# -------- 建立輸出文件 --------
def make_single_doc(f):
    return {
        "type": "single",
        "school": f["school"],
        "department": f["department"],
        "year": f["year"],
        "question_number": f["question_number"],
        "question_text": f["question_text"],
        "options": f["options"],
        "answer": f["answer"],
        "answer_type": f["question_type"],
        "image_file": f["image_file"],
    }


def make_group_doc(items, prefix):
    school = collapse_meta_from_flat(items, "school")
    dept = collapse_meta_from_flat(items, "department")
    year = collapse_meta_from_flat(items, "year")

    # 自動提取真正的 group_question_text
    true_prefix = extract_clean_prefix(prefix)

    sub_list = []
    for it in items:
        full_text = it["question_text"]
        suffix = full_text[len(true_prefix):].strip() if full_text.startswith(true_prefix) else full_text
        if not suffix and not KEEP_EMPTY_SUBTEXT:
            suffix = f"[{it['question_number']}]"

        sub_list.append({
            "question_number": it["question_number"],
            "question_text": suffix,
            "options": it["options"],
            "answer": it["answer"],
            "answer_type": it["question_type"],
            "image_file": it["image_file"],
        })

    return {
        "type": "group",
        "school": school,
        "department": dept,
        "year": year,
        "group_question_text": true_prefix,
        "sub_questions": sub_list
    }


def extract_clean_prefix(prefix):
    """
    嘗試從共同前綴中抽出整潔的 group_question_text。
    遇到 '\n\n' 就視為敘述段落結束。
    """
    parts = prefix.split("\n\n")
    if len(parts) > 1:
        return parts[0].strip()
    return prefix.strip()



# -------- 主分組邏輯 --------
def group_questions(raw_questions, min_prefix_len=MIN_PREFIX_LEN):
    normalized_raw = normalize_input(raw_questions)
    flat = [flatten_for_group(q) for q in normalized_raw]

    meta_buckets = defaultdict(list)
    for f in flat:
        key = (
            f["school"] or "UNK_SCHOOL",
            f["department"] or "UNK_DEPT",
            f["year"] or "UNK_YEAR",
        )
        meta_buckets[key].append(f)

    result_docs = []

    for (school, dept, year), items in meta_buckets.items():
        items.sort(key=lambda x: int(x["question_number"]) if str(x["question_number"]).isdigit() else 9999)

        i = 0
        while i < len(items):
            current_group = [items[i]]
            base_prefix = items[i]["question_text"]

            j = i + 1
            while j < len(items):
                texts = [q["question_text"] for q in current_group + [items[j]]]
                prefix = longest_common_prefix(texts, min_prefix_len)

                if prefix == base_prefix or not prefix:
                    break

                if (
                    prefix == longest_common_prefix(texts, min_prefix_len)
                    and is_valid_group_prefix(prefix)
                ):
                    current_group.append(items[j])
                    j += 1
                else:
                    break

            # 判斷是否為合法題組（2 題以上、題號連號、題幹合適）
            if len(current_group) >= 2:
                numbers = [
                    int(q["question_number"]) for q in current_group
                    if str(q["question_number"]).isdigit()
                ]
                if are_consecutive_numbers(numbers):
                    result_docs.append(make_group_doc(current_group, prefix))
                    i = j
                    continue

            # 否則單題處理
            result_docs.append(make_single_doc(items[i]))
            i += 1

    return result_docs


# -------- main --------
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_questions = json.load(f)

    grouped = group_questions(raw_questions, min_prefix_len=MIN_PREFIX_LEN)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(grouped, f, ensure_ascii=False, indent=2)

    print(f"分組完成，共 {len(grouped)} 筆；輸出：{OUTPUT_FILE}")


if __name__ == "__main__":
    main()
