from argparse import ArgumentParser, Namespace
from logic import build_report
from pathlib import Path
import os
from moodle.auth import (
    restore_session,
    MoodleCredentials,
    authorize,
    serialize_session,
    MoodleCachedSession,
)
from moodle.exceptions import (
    OpeningSessionFileError,
    CorruptedSessionError,
    SavingSessionFileError,
    IncorrectCredentialsError,
)
from logic.constants import SESSION_FILE
from moodle.session import MoodleSession
from getpass import getpass


class CLI:
    '''Command Line Interface (CLI) for managing Moodle sessions and generating reports.'''

    def __init__(self, args: Namespace) -> None:
        '''Initialize the CLI with command-line arguments.'''

        self.__args = args

    async def run_cli(self) -> None:
        '''Run the CLI process to handle session management and report generation.

        This method tries to restore a cached session from the session file. If the session file is missing
        or corrupted, it prompts the user to sign in and then builds the report. If the session is valid, it
        directly builds the report.
        '''

        try:
            cached_session = await restore_session(SESSION_FILE)
        except OpeningSessionFileError:
            cached_session = await self.__sign_in()
            if cached_session:
                await self.__build_report(cached_session)
        except CorruptedSessionError:
            print("Данные сессии испорчены.")

            try:
                os.remove(SESSION_FILE)
            except Exception:
                pass

            cached_session = await self.__sign_in()
            if cached_session:
                await self.__build_report(cached_session)
        else:
            cached_session = await self.__get_valid_cached_session(cached_session)
            await self.__build_report(cached_session)

    async def __sign_in(self) -> MoodleCachedSession | None:
        login = input("Введите логин: ")
        password = getpass("Введите пароль: ")
        cached_session = await self.__init_new_session(login, password)

        return cached_session

    async def __get_valid_cached_session(
        self, cached_session: MoodleCachedSession
    ) -> MoodleCachedSession:
        while True:
            async with MoodleSession(cached_session) as session:
                if not await session.is_valid():
                    login = input(
                        f"Введите логин (нажмите Enter, чтобы оставить {cached_session.login}): "
                    )
                    login = login or cached_session.login

                    password = getpass("Введите пароль: ")
                    new_cached_session = await self.__init_new_session(login, password)

                    cached_session = new_cached_session or cached_session
                else:
                    return cached_session

    async def __build_report(self, cached_session: MoodleCachedSession) -> None:
        try:
            await build_report(
                cached_session, self.__args.course_url, None, self.__args.output
            )
        except Exception:
            print(
                "При создании отчёта произошла непредвиденная ошибка. Повторите попытку позднее."
            )
        else:
            print("Отчет успешно загружен.")

    @staticmethod
    async def __init_new_session(
        login: str, password: str
    ) -> MoodleCachedSession | None:
        credentials = MoodleCredentials(login, password)
        try:
            cached_session = await authorize(credentials)

        except IncorrectCredentialsError:
            print("Некорректный логин или пароль. Попробуйте снова.")
            return

        except ConnectionError:
            print(
                "Не удалось установить соединение с удаленным сервером. "
                "Проверьте подключение к интернету."
            )
            return

        try:
            await serialize_session(SESSION_FILE, cached_session)
        except SavingSessionFileError:
            print("Не удалось сохранить сессию в файл.")
        else:
            return cached_session


def parse_arguments() -> Namespace:
    '''Parse command-line arguments for the CLI application.

    Returns:
        Namespace: Parsed command-line arguments.
    '''

    arg_parser = ArgumentParser(
        prog="Amm-option-subjects-puller",
        description="Утилита для скачивания с платформы Moodle excel-файла, "
        "содержащего данные о предметах по выбору для факультета ПММ",
    )

    arg_parser.add_argument(
        "course_url",
        help="Ссылка на страницу курса в Moodle, содержащего данные опросов",
        type=str,
    )
    arg_parser.add_argument(
        "-o",
        "--output",
        default=str(Path().cwd()),
        help="Директория для сохранения результата",
        type=str,
    )

    return arg_parser.parse_args()
