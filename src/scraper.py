import json
import os
import re
from typing import Any, Dict, List

import pdfplumber


class CourseScraper:
    # --- CONFIGURATION: Courses that span 2 slots ---
    TWO_SLOT_COURSES = {
        "BUSINESS FINANCE",
        "ELECTRONICS WORKSHOP",
        "SCIENCE LAB II",
        "SCIENCE LAB 2",
    }

    # --- CONFIGURATION: Courses to completely ignore ---
    BLACKLIST_COURSES = {
        "PO2",
    }

    # --- CONFIGURATION: Force specific Semester-Half metadata ---
    HALF_OVERRIDES = {
        "INFORMATION AND COMMUNICATION": "BOTH",
        "ENGINEERING VIRTUAL REALITY SYSTEMS": "BOTH",
    }

    # --- CONFIGURATION: Specific typo fixes (Courses PDF side) ---
    NAME_CORRECTIONS = {
        "Distributed Systems Prerequisite: Operating Systems. Networks desirable": "Distributed Systems",
        "Continuous Variable QuantumInformation Theory and Computation": "Continuous Variable Quantum Information Theory and Computation",
        "TKHS-I": "Thinking and Knowing in the Human Sciences I",
        "TKHS - I": "Thinking and Knowing in the Human Sciences I",
        "Thinking and Knowing in the Human Sciences- I": "Thinking and Knowing in the Human Sciences I",
        "Thinking and Knowing in the Human Sciences - I": "Thinking and Knowing in the Human Sciences I",
        "Thinking and Knowing in the Human Sciences I": "Thinking and Knowing in the Human Sciences I",
        "Thinking and Knowing in the Human Sciences-I": "Thinking and Knowing in the Human Sciences I",
        "Value Education II": "Value Education II",
        "Value Education - II": "Value Education II",
        "Value Education-II": "Value Education II",
        "Science Lab II": "Science Lab II",
        "Science Lab 2": "Science Lab II",
        "Science Lab-II": "Science Lab II",
    }

    # --- CONFIGURATION: Search Aliases (Timetable PDF side) ---
    ALIAS_MAP = {
        "THINKING AND KNOWING IN THE HUMAN SCIENCES I": [
            "TKHS-I",
            "TKHS - I",
            "TKHS I",
        ],
        "VALUE EDUCATION II": ["VALUE EDUCATION II", "VALUE EDUCATION-II"],
        "SCIENCE LAB II": ["SCIENCE LAB II", "SCIENCE LAB 2", "SCIENCE LAB-II"],
    }

    def __init__(
        self, timetable_path: str = "timetable.pdf", courses_path: str = "courses.pdf"
    ):
        self.timetable_path = timetable_path
        self.courses_path = courses_path

    def clean_text(self, text: str) -> str:
        if not text:
            return ""

        text = text.replace("\n", " ").replace("\r", " ")
        text = re.sub(r"\s+", " ", text)

        text = re.sub(r"\bIntro[\.:]?\b", "Introduction", text, flags=re.IGNORECASE)
        text = text.replace("&", " and ")
        text = re.sub(r"\bAnd\b", "and", text, flags=re.IGNORECASE)

        # Normalize Roman Numerals (Space + I/II)
        text = re.sub(r"\s*-\s*(I|II)\b", r" \1", text)
        text = re.sub(r"\s+(I|II)$", r" \1", text)

        text = re.sub(r"\s+", " ", text).strip()
        return text

    def parse_half_from_string(self, text: str) -> str:
        upper = text.upper()
        if any(x in upper for x in ["H1+H2", "H1/H2", "H1&H2", "(H1,H2)", "H1 AND H2"]):
            return "BOTH"

        has_h1 = bool(re.search(r"\(H1\)| H1 |^H1 | H1$", upper)) or ("(H1)" in upper)
        has_h2 = bool(re.search(r"\(H2\)| H2 |^H2 | H2$", upper)) or ("(H2)" in upper)

        if has_h1 and not has_h2:
            return "H1"
        if has_h2 and not has_h1:
            return "H2"
        return "BOTH"

    def get_official_name(self, raw_name: str) -> str:
        if raw_name in self.NAME_CORRECTIONS:
            raw_name = self.NAME_CORRECTIONS[raw_name]

        def replacement(match):
            content = match.group(1).strip()
            content_upper = content.upper()

            if re.match(r"^H[12]?(\s*(AND|[+&/])\s*H[12]?)?$", content_upper):
                return ""
            if content_upper.startswith("MAX") or content_upper.startswith("LIMIT"):
                return ""
            if content.isdigit():
                return ""
            return match.group(0)

        cleaned = re.sub(r"\(([^)]*)\)", replacement, raw_name)
        cleaned = cleaned.replace("  ", " ").strip()
        cleaned = cleaned.rstrip(".,").strip()
        return cleaned

    def get_search_term(self, official_name: str) -> str:
        return official_name.strip()

    def get_master_course_list(self) -> Dict[str, Dict]:
        registry = {}
        if not os.path.exists(self.courses_path):
            print(f"Error: {self.courses_path} not found.")
            return {}

        try:
            with pdfplumber.open(self.courses_path) as pdf:
                for page_idx in range(7):
                    if page_idx >= len(pdf.pages):
                        break
                    page = pdf.pages[page_idx]
                    tables = page.extract_tables()

                    for table in tables:
                        if not table or len(table[0]) < 3:
                            continue

                        start_row = 1 if page_idx == 0 else 0
                        name_idx = 2

                        for row in table[start_row:]:
                            if len(row) <= name_idx:
                                continue
                            raw_name = row[name_idx]
                            if not raw_name:
                                continue

                            raw_name_clean = self.clean_text(raw_name)
                            if len(raw_name_clean) < 3 or raw_name_clean.isdigit():
                                continue

                            official_name = self.get_official_name(raw_name_clean)

                            if official_name in self.BLACKLIST_COURSES:
                                continue

                            half_tag = self.parse_half_from_string(raw_name_clean)
                            if official_name.upper() in self.HALF_OVERRIDES:
                                half_tag = self.HALF_OVERRIDES[official_name.upper()]

                            search_term = self.get_search_term(official_name)

                            if len(search_term) < 2:
                                continue

                            registry[search_term] = {
                                "official_name": official_name,
                                "half": half_tag,
                            }
        except Exception as e:
            print(f"Error parsing courses.pdf: {e}")
            return {}

        return registry

    def extract_courses(self) -> List[Dict[str, Any]]:
        registry_map = self.get_master_course_list()
        if not registry_map:
            return []

        courses_db = {}
        for term, meta in registry_map.items():
            courses_db[term] = {
                "id": meta["official_name"],
                "name": meta["official_name"],
                "half": meta["half"],
                "sessions": [],
            }

        sorted_search_terms = sorted(registry_map.keys(), key=len, reverse=True)

        try:
            if os.path.exists(self.timetable_path):
                with pdfplumber.open(self.timetable_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        days = (
                            ["Mon", "Tue", "Wed"] if i == 0 else ["Thu", "Fri", "Sat"]
                        )
                        self._scan_page(page, days, courses_db, sorted_search_terms)
        except Exception as e:
            print(f"Error reading timetable: {e}")

        final_courses = list(courses_db.values())
        final_courses.sort(key=lambda x: x["name"])
        return final_courses

    def _merge_broken_rows(self, raw_table: List[List[str]]) -> List[List[str]]:
        merged_table = []
        if not raw_table:
            return []

        for row in raw_table:
            clean_row = [self.clean_text(cell) if cell else "" for cell in row]

            is_continuation = (not clean_row[0]) and any(clean_row)

            if is_continuation and merged_table:
                last_row = merged_table[-1]
                for i in range(len(clean_row)):
                    if clean_row[i]:
                        if i < len(last_row):
                            if last_row[i]:
                                last_row[i] += " " + clean_row[i]
                            else:
                                last_row[i] = clean_row[i]
            else:
                merged_table.append(clean_row)
        return merged_table

    def _scan_page(
        self, page, days: List[str], courses_db: Dict, search_terms: List[str]
    ):
        raw_table = page.extract_table()
        if not raw_table:
            return

        clean_table = self._merge_broken_rows(raw_table)
        current_day_idx = 0
        SLOT_MAP = {1: 1, 2: 2, 3: 3, 4: 6, 5: 7, 6: 8}

        for row in clean_table:
            if current_day_idx >= len(days):
                break

            if len(row) < 7 or "8:30" in row[1]:
                continue

            day_name = days[current_day_idx]

            for slot_num, col_idx in SLOT_MAP.items():
                if col_idx >= len(row):
                    continue
                cell_content = row[col_idx]
                if not cell_content:
                    continue
                temp_content_upper = cell_content.upper()

                for term in search_terms:
                    term_upper = term.upper()

                    match_found = term_upper in temp_content_upper
                    matched_text = term_upper

                    if not match_found:
                        aliases = self.ALIAS_MAP.get(term_upper, [])
                        for alias in aliases:
                            if alias in temp_content_upper:
                                match_found = True
                                matched_text = alias
                                break

                    if match_found:
                        local_half = self.parse_half_from_string(cell_content)
                        current_half = courses_db[term]["half"]
                        course_id = courses_db[term]["id"].upper()

                        if course_id in self.HALF_OVERRIDES:
                            courses_db[term]["half"] = self.HALF_OVERRIDES[course_id]
                        else:
                            if current_half == "BOTH" and local_half != "BOTH":
                                courses_db[term]["half"] = local_half

                        def add_session(s_num):
                            sess = {"day": day_name, "slot": s_num}
                            if sess not in courses_db[term]["sessions"]:
                                courses_db[term]["sessions"].append(sess)

                        add_session(slot_num)

                        is_two_slot = False
                        for ts_name in self.TWO_SLOT_COURSES:
                            if ts_name in term_upper:
                                is_two_slot = True
                                break
                        if not is_two_slot and term_upper in self.ALIAS_MAP:
                            for alias in self.ALIAS_MAP[term_upper]:
                                for ts_name in self.TWO_SLOT_COURSES:
                                    if ts_name in alias:
                                        is_two_slot = True
                                        break

                        if is_two_slot and slot_num < 6:
                            add_session(slot_num + 1)

                        temp_content_upper = temp_content_upper.replace(
                            matched_text, " " * len(matched_text)
                        )

            current_day_idx += 1


# --- Helpers ---
def save_courses_to_json(courses: List[Dict], filename: str = "courses.json"):
    try:
        with open(filename, "w") as f:
            json.dump(courses, f, indent=4)
        print(f"Saved {len(courses)} courses to {filename}")
    except Exception as e:
        print(f"Error saving JSON: {e}")


def load_courses_from_json(filename: str = "courses.json") -> List[Dict]:
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception:
        return []


def load_manual_courses(filename: str = "courses_manual.json") -> List[Dict]:
    try:
        if not os.path.exists(filename):
            return []
        with open(filename, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading manual courses: {e}")
        return []


def get_course_data(
    json_path: str = "courses.json",
    manual_path: str = "courses_manual.json",
    timetable_pdf: str = "timetable.pdf",
    courses_pdf: str = "courses.pdf",
    force_scrape: bool = False,
) -> List[Dict]:
    """
    1. Scrapes or loads courses.json.
    2. Loads courses_manual.json.
    3. Merges them. Manual entries can OVERWRITE or DELETE scraped entries.
    """
    should_scrape = force_scrape or not os.path.exists(json_path)

    scraped_data = []

    # 1. Get Scraped Data
    if should_scrape:
        print("Scraping fresh data...")
        scraper = CourseScraper(timetable_path=timetable_pdf, courses_path=courses_pdf)
        scraped_data = scraper.extract_courses()
        if scraped_data:
            save_courses_to_json(scraped_data, json_path)
    else:
        scraped_data = load_courses_from_json(json_path)

    # 2. Get Manual Data
    manual_data = load_manual_courses(manual_path)

    # 3. Merge Logic
    courses_map = {c["id"]: c for c in scraped_data}

    if manual_data:
        print(f"Found {len(manual_data)} manual entries. Merging...")
        for manual_c in manual_data:
            cid = manual_c.get("id")
            if cid:
                # --- NEW DELETION LOGIC ---
                if manual_c.get("delete") is True:
                    # Remove the course if it exists
                    courses_map.pop(cid, None)
                else:
                    # Overwrite/Add the course
                    courses_map[cid] = manual_c

    # Convert back to list and sort
    final_courses = list(courses_map.values())
    final_courses.sort(key=lambda x: x["name"])

    return final_courses
