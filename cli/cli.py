import argparse
import re
import os
from pathlib import Path

from logic import build_report
from moodle.auth import restore_session, MoodleCredentials, authorize, serialize_session, \
    MoodleCachedSession
from moodle.exceptions import (
    OpeningSessionFileError,
    CorruptedSessionError,
    SavingSessionFileError,
    IncorrectCredentialsError
)
from logic.constants import SESSION_FILE
from moodle.session import MoodleSession


arg_parser = argparse.ArgumentParser(
    prog='Amm-option-subjects-puller',
    description='Утилита для скачивания с платформы Moodle excel-файла, '
                'содержащего данные о предметах по выбору для факультета ПММ'
)

arg_parser.add_argument(
    'course_url',
    help='Ссылка на страницу курса в Moodle, содержащего данные опросов',
    type=str
)
arg_parser.add_argument(
    '-o',
    '--output',
    default=str(Path().cwd()),
    help='Директория для сохранения результата',
    type=str
)


class CLI:
    def __init__(self, parser: argparse.ArgumentParser = arg_parser):
        self.parser = parser
        self.__args = self.parser.parse_args()

    @staticmethod
    async def __init_new_session(login: str, password: str) -> MoodleCachedSession | None:
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

    async def __sign_in(self) -> MoodleCachedSession | None:
        login = input("Введите логин\n")
        password = input("Введите пароль\n")
        cached_session = await self.__init_new_session(login, password)

        return cached_session

    async def __get_valid_cached_session(self, cached_session: MoodleCachedSession) -> MoodleCachedSession:
        session = MoodleSession(cached_session)
        while not await session.is_valid():
            login = input(f"Введите логин (нажмите Enter, чтобы оставить {cached_session.login})\n")
            if not login:
                login = cached_session.login
            password = input("Введите пароль\n")
            new_cached_session = await self.__init_new_session(login, password)
            if new_cached_session:
                session = MoodleSession(cached_session)
                cached_session = new_cached_session

        return cached_session

    @staticmethod
    def __get_course_id(course_url: str) -> str:
        match = re.search(r'id=(\d+)', course_url)
        if not match:
            raise ValueError("Unable to get course identifier.")

        return match.group(1)

    async def __build_report(self, cached_session: MoodleCachedSession) -> None:
        if not cached_session:
            print("Отсутсвуют данные сессии.")
            return

        try:
            course_id = self.__get_course_id(self.__args.course_url)
        except ValueError:
            print(
                f"Невозможно получить идентификатор курса. "
                f"Проверьте корректность ссылки {self.__args.course_url}."
            )
            return

        try:
            await build_report(cached_session, course_id, self.__args.output)
        except Exception:
            print("При создании отчёта произошла непредвиденная ошибка. Повторите попытку позднее.")
        else:
            print("Отчет успешно загружен.")

    async def run_cli(self) -> None:
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