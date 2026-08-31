from asyncio import run

from cli.cli import CLI, parse_arguments


def main() -> None:
    cli = CLI(parse_arguments())
    run(cli.run_cli())


if __name__ == "__main__":
    main()
