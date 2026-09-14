"""
Dynamic Resume Matcher: Evaluates job postings against Rehman Sha's profile
without rigid keyword hardcoding.

Handles:
- Conventional titles: Software Engineer, SDE 1, SDE 2, Full Stack Developer
- Unconventional titles: Member of Technical Staff (MTS 1 / MTS 2), Application Engineer,
  Product Engineer, Systems Engineer, Platform Engineer, Technical Associate
- Department context: Identifies engineering roles even when companies use creative titles
- Seniority filter: Safely separates true seniors (Staff SWE, Principal, Lead) from
  entry/mid-level titles like 'Member of Technical Staff 1'
"""

import re
from typing import Tuple

# Seniority titles that exceed Rehman's 1.5 - 2 years experience.
# Note: 'staff' is scoped to avoid falsely rejecting 'Member of Technical Staff (MTS 1/2)'
SENIOR_EXCLUSIONS = [
    r"\bsenior\b",
    r"\bsr\.?\b",
    r"\blead\b",
    r"\bprincipal\b",
    r"\bdirector\b",
    r"\bvice\s+president\b",
    r"\bvp\b",
    r"\barchitect\b",
    r"\bmanager\b",
    r"\bhead\s+of\b",
    r"\bdistinguished\b",
    r"\bexecutive\b",
    # Specific level markers for senior tiers
    r"\bsde\s*(?:iii|iv|3|4|5)\b",
    r"\bsoftware\s+engineer\s*(?:iii|iv|3|4|5)\b",
    r"\bmts\s*(?:iii|iv|3|4|5)\b",
    r"\bmember\s+of\s+technical\s+staff\s*(?:iii|iv|3|4|5)\b",
    # Matches 'Staff Engineer' / 'Staff Software Engineer' while keeping 'Member of Technical Staff'
    r"\bstaff\s+(?:software|engineer|developer|architect|system|platform|devops)\b",
]

# Non-technical business functions to exclude
NON_TECH_EXCLUSIONS = [
    r"\bsales\b",
    r"\bmarketing\b",
    r"\brecruiter\b",
    r"\btalent\s+acquisition\b",
    r"\bhuman\s+resources\b",
    r"\bhr\b",
    r"\bfinance\b",
    r"\baccounting\b",
    r"\blegal\b",
    r"\bbusiness\s+development\b",
    r"\bbdr\b",
    r"\bsdr\b",
    r"\bpresales\b",
    r"\bpre-sales\b",
    r"\baccount\s+executive\b",
    r"\bcontent\s+writer\b",
    r"\boffice\s+manager\b",
    r"\bcustomer\s+support\s+representative\b",
    r"\btelecaller\b",
]

# Universal functional engineering roots (covers 99% of tech titles)
TECH_FUNCTIONAL_ROOTS = [
    r"\bengineer\b",
    r"\bdeveloper\b",
    r"\bprogrammer\b",
    r"\bmember\s+of\s+technical\s+staff\b",
    r"\bmts(?:\s*[-_]?\s*(?:i|1|ii|2|associate|junior))?\b",
    r"\bsde(?:\s*[-_]?\s*(?:i|1|ii|2|associate|junior))?\b",
    r"\bswe(?:\s*[-_]?\s*(?:i|1|ii|2|associate|junior))?\b",
    r"\bfull[\s-]?stack\b",
    r"\bfront[\s-]?end\b",
    r"\bback[\s-]?end\b",
    r"\bweb\b",
    r"\bcloud\b",
    r"\bplatform\b",
    r"\bsystems?\b",
    r"\bapplication\b",
    r"\bdata\b",
    r"\bai\b",
    r"\bml\b",
    r"\bdevops\b",
    r"\bsdet\b",
    r"\bqa\b",
    r"\bmobile\b",
    r"\bios\b",
    r"\bandroid\b",
    r"\bflutter\b",
    r"\bswift\b",
]

# Department keywords indicating technical/engineering division
ENGINEERING_DEPARTMENTS = [
    "engineering",
    "technology",
    "r&d",
    "research and development",
    "software",
    "product development",
    "information technology",
    "it",
    "platform",
    "data science",
    "core tech",
]

# Candidate's core tech stack from resume
CORE_STACK_PATTERNS = [
    (r"\b(?:react|react\.js)\b", "React.js Stack Match", 95),
    (r"\b(?:react\s*native)\b", "React Native Match", 94),
    (r"\b(?:flutter|android|ios|swift|mobile)\b", "Mobile Stack Match", 90),
    (r"\b(?:node|node\.js|express)\b", "Node.js Stack Match", 95),
    (r"\b(?:java|spring\s*boot)\b", "Java / Spring Boot Stack Match", 95),
    (r"\bpython\b", "Python Stack Match", 95),
    (r"\bfull[\s-]?stack\b", "Full-Stack Match", 95),
    (r"\b(?:rag|genai|generative\s+ai|llm|pgvector)\b", "GenAI / RAG Match", 95),
    (r"\b(?:frontend|front[\s-]end)\b", "Frontend Match", 92),
    (r"\b(?:backend|back[\s-]end)\b", "Backend Match", 92),
    (r"\bweb\s+developer\b", "Web Developer Match", 90),
]

def evaluate_resume_match(title: str, department: str = "") -> Tuple[bool, int, str]:
    """
    Dynamically classifies whether a job matches Rehman Sha's background (1.5 - 2 yrs SWE).
    Does not require hardcoding every unconventional title synonym.

    Returns: (is_match: bool, score: int, match_reason: str)
    """
    t_clean = title.lower().strip()
    d_clean = department.lower().strip() if department else ""
    combined = f"{t_clean} {d_clean}".strip()

    # 1. Negative Filter: Drop non-tech functions (sales, hr, legal, marketing)
    for pat in NON_TECH_EXCLUSIONS:
        if re.search(pat, combined):
            return False, 0, "Excluded: Non-Tech"

    # 2. Negative Filter: Drop true senior/lead/architect roles (5+ yrs)
    # Exclude standalone 'staff' (Staff SWE, Staff SRE, etc.) while preserving 'Member of Technical Staff'
    if "staff" in t_clean and "member of technical staff" not in t_clean:
        return False, 0, "Excluded: Staff level"

    for pat in SENIOR_EXCLUSIONS:
        if re.search(pat, t_clean):
            return False, 0, "Excluded: Senior/Lead level"

    # 3. High-Priority Positive Signal: Exact Stack Match from Rehman's Resume
    for pat, reason, score in CORE_STACK_PATTERNS:
        if re.search(pat, combined):
            return True, score, reason

    # 4. Dynamic Technical Root Match (Handles MTS, Application Engineer, Product Engineer, etc.)
    is_tech_root = any(re.search(pat, t_clean) for pat in TECH_FUNCTIONAL_ROOTS)
    is_eng_dept = any(dept_word in d_clean for dept_word in ENGINEERING_DEPARTMENTS)

    if is_tech_root or is_eng_dept:
        # Provide clean, descriptive match tag based on semantic category
        if "member of technical staff" in t_clean or re.search(r"\bmts\b", t_clean):
            return True, 90, "Technical Staff (MTS) Match"
        elif "application" in t_clean:
            return True, 88, "Application Engineering Match"
        elif "product" in t_clean and "engineer" in t_clean:
            return True, 88, "Product Engineering Match"
        elif "platform" in t_clean:
            return True, 88, "Platform Engineering Match"
        elif any(k in t_clean for k in ["mobile", "android", "ios", "flutter", "swift", "react native"]):
            return True, 88, "Mobile Engineering Match"
        elif "sde" in t_clean or "software" in t_clean:
            return True, 90, "Software Engineering Match"
        elif "systems" in t_clean:
            return True, 86, "Systems Engineering Match"
        elif is_eng_dept:
            return True, 85, f"Engineering Dept ({department or 'Tech'})"
        else:
            return True, 85, "General Tech Match"

    return False, 0, "Not matched to tech profile"
