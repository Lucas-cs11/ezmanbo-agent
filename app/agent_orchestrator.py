import uuid
from .requirement_parser import parse_requirement
from .ezplm_client import search_parts, find_replacements
from .scoring import score_candidates
from .evidence import build_evidence
from .report_generator import build_report
from .schemas import SelectionReport


def analyze(user_input: str) -> SelectionReport:
    req = parse_requirement(user_input)
    parts = search_parts(req)
    scored = score_candidates(req, parts)
    evidence = build_evidence(scored)
    report = build_report(req, scored, evidence)
    return report


def replacement_report(original_part_number: str):
    replacements = find_replacements(original_part_number)
    # create a simple replacement report using scoring
    scored = score_candidates(None, replacements) if replacements else []
    return {
        "original_part_number": original_part_number,
        "replacement_candidates": [s.part.dict() for s in scored],
    }

