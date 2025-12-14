"""Static program defaults for compulsory courses."""

from typing import Dict, List

YEAR_OPTIONS: List[str] = ["UG1", "UG2"]
BRANCH_OPTIONS: List[str] = ["CSX", "ECX", "CLD", "CGD", "CHD", "CND", "LE-CSD", "LE-ECD"]

COMPULSORY_COURSES: Dict[str, Dict[str, List[str]]] = {
    "UG1": {
        "CSX": [
            "Introduction to Software Systems",
            "Data Structures and Algorithms",
            "Computer Systems Organization",
            "Linear Algebra",
            "Introduction to IoT",
            "Arts-2"
        ],
        "ECX": [
            "Analog Electronic Circuits",
            "Information and Communication",
            "Data Structures and Algorithms",
            "Linear Algebra",
            "Arts-2"
        ],
        "CND": [
            "Introduction to Software Systems",
            "Data Structures and Algorithms",
            "Linear Algebra",
            "Computing in Sciences II",
            "Classical Mechanics",
            "Electrodynamics",
            "General and Structural Chemistry",
            "Arts-2"
        ],
        "CLD": [
            "Linear Algebra",
            "Introduction to Software Systems",
            "Data Structures and Algorithms",
            "Computer Systems Organization",
            "Introduction to Linguistics II",
            "Computational Linguistics 1",
            "Arts-2"
        ],
        "CHD": [
            "Linear Algebra",
            "Introduction to Software Systems",
            "Data Structures and Algorithms",
            "Making of Contemporary World",
            "Thinking and Knowing in the Human Sciences I",
            "Arts-2"
        ],
        "CGD": [
            "Linear Algebra",
            "Introduction to Software Systems",
            "Data Structures and Algorithms",
            "Computer Systems Organization",
            "Introduction to IoT",
            "Arts-2",
            "Introduction to Spatial Sciences and Technology"
        ]
    },
    "UG2": {
        "CSX": [
            "Design and Analysis of Software Systems",
            "Introduction to Human Sciences B",
            "Machine, Data and Learning",
            "Science II A",
            "Value Education II"
        ],
        "ECX": [
            "Communication Theory",
            "Introduction to Processor Architecture",
            "Introduction to Human Sciences A",
            "Value Education II"
        ],
        "LE-CSD": [
            "Design and Analysis of Software Systems",
            "Introduction to Human Sciences B",
            "Machine, Data and Learning",
            "Value Education II"
        ],
        "LE-ECD": [
            "Communication Theory",
            "Introduction to Human Sciences A",
            "Introduction to Processor Architecture",
            "Value Education II"
        ],
        "CLD": [
            "Introduction to Human Sciences A",
            "Machine, Data and Learning",
            "Design and Analysis of Software Systems",
            "Language Typology and Universals",
            "Introduction to NLP",
            "Digital Signal Analysis",
            "Value Education II"
        ],
        "CHD": [
            "Computer Systems Organization",
            "Machine, Data and Learning",
            "Design and Analysis of Software Systems",
            "Research Methods in Human Sciences",
            "Science, Technology and Society",
            "Knowing India Through Data",
            "Value Education II"
        ],
        "CND": [
            "Machine, Data and Learning",
            "Introduction to Human Sciences A",
            "Design and Analysis of Software Systems",
            "Thermodynamics",
            "Statistical Mechanics",
            "Biomolecular Structures",
            "Organic Chemistry",
            "Science Lab II",
            "Value Education II"
        ],
        "CGD": [
            "Machine, Data and Learning",
            "Introduction to Human Sciences A",
            "Design and Analysis of Software Systems",
            "Optical Remote Sensing",
            "Value Education II"
        ]
    }
}


def get_compulsory_courses(year: str, branch: str) -> List[str]:
    """Return the list of compulsory course IDs for the given track."""
    return COMPULSORY_COURSES.get(year, {}).get(branch, [])
