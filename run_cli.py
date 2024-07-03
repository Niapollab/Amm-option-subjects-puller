from asyncio import run
from cli.cli import CLI, parse_arguments


async def main() -> None:
    cli = CLI(parse_arguments())
    await cli.run_cli()


if __name__ == "__main__":
    run(main())
