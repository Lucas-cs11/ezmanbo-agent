#!/usr/bin/env python3
from app.requirement_parser import parse_requirement


def main():
    examples = [
        "我需要一个 12V 转 5V、3A 的车规级降压方案，工作温度 -40°C 到 125°C，优先考虑国产替代和低供应链风险。",
        "需要 24V 转 12V、2A 的降压方案，工作温度 -40°C 到 85°C。",
    ]
    for ex in examples:
        rc = parse_requirement(ex)
        print("INPUT:\n", ex)
        try:
            print("PARSE:\n", rc.dict())
        except Exception:
            # dataclass fallback
            print(rc)
        print("---\n")


if __name__ == '__main__':
    main()

