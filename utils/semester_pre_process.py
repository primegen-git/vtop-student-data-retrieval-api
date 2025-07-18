from typing import Dict


def semester_pre_process(semester_data: Dict[str, str], reg_no: str) -> Dict[str, Dict[str, str]]:
    """
    Pre-processes the semester data to include detailed information about each semester.

    Args:
        semester_data (Dict[str, str]): Raw semester data with semester codes as keys and names as values.
        reg_no (str): Registration number to determine the admission year.

    Returns:
        Dict[str, Dict[str, str]]: Processed semester data with additional details.
    """

    num_str_map = {
        0: "Extra",
        1: "1st",
        2: "2nd",
        3: "3rd",
        4: "4th",
        5: "5th",
        6: "6th",
        7: "7th",
        8: "8th",
        9: "9th",
        10: "10th"
    }

    adm_yr = int("20" + reg_no[:2])
    ind = 0
    ans = {}

    for sem_code, sem_name in semester_data.items():
        detail = "{study_year} Year of study in degree. {yr_sem} sem in this year. {cumulative_sem} semester so far in entire degree."
        ind += 1

        sem_yr = int(sem_code[2:6])
        study_yr = sem_yr - adm_yr + 1

        if "fall" in sem_name.lower():
            sem_num = 1
        elif "winter" in sem_name.lower():
            sem_num = 2
        else:
            sem_int = 0
            sem_num = 0

        cumulative_num = (study_yr - 1) * 2 + sem_num

        detail = detail.format(
            study_year=num_str_map[study_yr],
            yr_sem=num_str_map[sem_num],
            cumulative_sem=num_str_map[cumulative_num]
        )

        ans[sem_code] = {
            "name": sem_name,
            "detail": {
                "study_year": f"This is the {num_str_map[study_yr]} year since admission ({adm_yr}).",
                "semester_in_year": f"This semester is the {num_str_map[sem_num]} semester of that academic year.",
                "cumulative_semester": f"This is the {num_str_map[cumulative_num]} semester overall since starting the degree."
            }
        }

    return ans


output_format = {
    "CH20232401": {
        "name": "Fall Semester 2023-24",
        "detail": {
            "study_year": "This is the 2nd year since admission ({adm_year}).",
            "semester_in_year": "This semester is the 1st semester of that academic year.",
            "cumulative_semester": "This is the 3rd semester overall since starting the degree.",
        }
    }
}

if __name__ == "__main__":
    # Example usage
    semesters = {
        "CH20252601": "Fall Semester 2025-26",
        "CH20242505": "Winter Semester 2024-25",
        "CH20242501": "Fall Semester 2024-25",
        "CH20232405": "Winter Semester 2023-24",
        "CH20232401": "Fall Semester 2023-24",
        "CH20222323": "Winter Semester I year 2022-23",
        "CH20222317": "Fall Semester I year 2022-23"
    }

    from pprint import pprint
    pprint(semesters, sort_dicts=False, width=120)
    processed_data = semester_pre_process(semesters, "22BCE1519")
    pprint(processed_data, sort_dicts=False, width=120)

    print("\n"*4)
    import json
    out1 = json.dumps(processed_data)
    print(out1)
    print(len(out1))

    out_2 = json.dumps(processed_data, separators=(',', ':'))
    print(out_2)
    print(len(out_2))
