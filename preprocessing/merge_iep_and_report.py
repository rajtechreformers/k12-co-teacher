import json
import uuid
import hashlib
from extract_iep import extract_student_info_from_iep
from extract_psych_reports import extract_psychological_report

def deduped_merge_list(list1, list2):
    """given two lists, merges into one, removing duplicates"""
    seen = set()
    result = []
    for item in list1 + list2:
        key = item.lower().strip() if isinstance(item, str) else str(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

def merge_profiles(psych_data, iep_data):
    merged = {
        "first_name": psych_data.get("first_name"),
        "last_name": psych_data.get("last_name"),
        "student_id": psych_data.get("student_id"),
        "iep_goals": deduped_merge_list(iep_data.get("iep_goals", []), psych_data.get("iep_goals", [])),
        "accommodations": deduped_merge_list(iep_data.get("accommodations", []), psych_data.get("accommodations", [])),
        "learning_styles": psych_data.get("learning_styles", []),
        "disabilities": psych_data.get("disabilities", []),
        "services": iep_data.get("services", []),
        "placement": iep_data.get("placement"),
        "interviews": psych_data.get("interviews", {}),
        "observations": psych_data.get("observations", {})
    }
    return merged

if __name__ == "__main__":
    # 1. generate student id for now
    # 2. extract from iep and psych report
    # 3. merge to create one profile w/ no duplicate info

    full_uuid = str(uuid.uuid4())
    student_id = hashlib.sha1(full_uuid.encode()).hexdigest()[:5]
    path_to_report = "data/SLD Report.pdf"
    path_to_iep = "data/IEP_Redacted_Johansson.pdf"
    extract_psychological_report(path_to_report, student_id)
    extract_student_info_from_iep(path_to_iep, student_id)

    with open(f"{student_id}/{student_id}_student_profile.json") as f:
        psych = json.load(f)
    with open(f"{student_id}/{student_id}_merged_iep_profile.json") as f:
        iep = json.load(f)
    final = merge_profiles(psych, iep)
    with open(f"{student_id}/{student_id}_final_student_profile.json", "w") as f:
        json.dump(final, f, indent=2)
