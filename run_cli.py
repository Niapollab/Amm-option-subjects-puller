from asyncio import run

from cli.cli import CLI


async def main() -> None:
    cli = CLI()
    await cli.run_cli()


if __name__ == '__main__':
    run(main())
