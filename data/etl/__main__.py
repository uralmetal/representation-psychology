from etl.extract import build
from etl.report import write
from etl.validate import validate


def main() -> None:
    dataset = build()
    errors = validate(dataset)
    write(dataset, errors)
    print(f"works={len(dataset['works'])} scenes={len(dataset['scenes'])} warnings={len(dataset['warnings'])}")
    for warning in dataset["warnings"]:
        print(f"warning: {warning}")
    if errors:
        for error in errors:
            print(f"error: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
