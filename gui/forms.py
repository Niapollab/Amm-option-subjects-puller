import os
from asyncio import run
from contextlib import suppress
from typing import Any

from CTkMessagebox import CTkMessagebox
from customtkinter import (
    CTk,
    CTkBaseClass,
    CTkButton,
    CTkEntry,
    CTkLabel,
    CTkToplevel,
    StringVar,
    filedialog,
)

from gui.constants import FORM_SIZES, SCALE_FACTOR
from gui.progress import ProgressHandlerContext
from gui.utils import DisabledContext
from logic.builder import build_report
from logic.constants import SESSION_FILE
from moodle.auth import (
    MoodleCachedSession,
    MoodleCredentials,
    authorize,
    restore_session,
    serialize_session,
)
from moodle.session import MoodleSession


class LoginDialog:
    """Dialog for user login to Moodle."""

    _ctk: CTkToplevel
    _login: StringVar
    _password: StringVar
    _is_signed_in: bool

    def __init__(self, master: Any, login: str | None) -> None:
        """Initialize the login dialog.

        Args:
            master (Any): The parent window.
            login (str | None): The pre-filled login (username) if available.
        """

        self._ctk = CTkToplevel(master)
        self._login = StringVar(self._ctk, login or "")
        self._password = StringVar(self._ctk)
        self._is_signed_in = False

        self._init_style()
        master.wait_window(self._ctk)

    @property
    def credentials(self) -> MoodleCredentials | None:
        """Get the user's credentials if signed in.

        Returns:
            MoodleCredentials | None: The user's credentials if signed in, otherwise None.
        """

        return (
            MoodleCredentials(self._login.get(), self._password.get())
            if self._is_signed_in
            else None
        )

    def _init_style(self) -> None:
        ctk = self._ctk
        ctk.title("Вход")
        ctk.geometry(FORM_SIZES)

        username_label = CTkLabel(ctk, text="Логин")
        username_label.pack(pady=(SCALE_FACTOR, 0), fill="x")

        username_entry = CTkEntry(ctk, textvariable=self._login)
        username_entry.pack(pady=(SCALE_FACTOR, 0), fill="x")

        password_label = CTkLabel(ctk, text="Пароль")
        password_label.pack(pady=(SCALE_FACTOR, 0), fill="x")

        password_entry = CTkEntry(ctk, show="*", textvariable=self._password)
        password_entry.pack(pady=(SCALE_FACTOR, 0), fill="x")

        login_button = CTkButton(ctk, text="Войти", command=self._sign_in)
        login_button.pack(pady=(2 * SCALE_FACTOR, 0), fill="x")

    def _sign_in(self) -> None:
        self._is_signed_in = True
        self._ctk.destroy()


class MainForm:
    """Main application form for creating a Moodle report."""

    _ctk: CTk
    _course_id: StringVar
    _directory: StringVar
    _clickable: list[CTkBaseClass]
    _cached_session: MoodleCachedSession | None
    _is_destroyed: bool

    def __init__(self) -> None:
        """Initialize the main form."""

        self._is_destroyed = False
        self._ctk = CTk()
        self._course_id = StringVar()
        self._directory = StringVar(self._ctk, os.getcwd())
        self._clickable = []

        self._init_style()
        self._init_session()
        self._ensure_session_init()

    def mainloop(self) -> None:
        """Start the main event loop for the form."""

        if not self._is_destroyed:
            self._ctk.mainloop()

    def _init_style(self) -> None:
        ctk = self._ctk
        ctk.title("Создание отчета")
        ctk.geometry(FORM_SIZES)
        ctk.resizable(width=False, height=False)

        ctk.grid_columnconfigure(0, weight=1)

        course_label = CTkLabel(ctk, text="Ссылка на курс или идентификатор:")
        course_label.grid(
            row=0,
            column=0,
            columnspan=2,
            padx=(SCALE_FACTOR, SCALE_FACTOR),
            pady=(SCALE_FACTOR, 0),
            sticky="ew",
        )

        course_entry = CTkEntry(ctk, textvariable=self._course_id)
        course_entry.grid(
            row=1,
            column=0,
            columnspan=2,
            padx=(SCALE_FACTOR, SCALE_FACTOR),
            pady=(SCALE_FACTOR, 0),
            sticky="ew",
        )

        output_label = CTkLabel(ctk, text="Путь к выходной директории:")
        output_label.grid(
            row=2,
            column=0,
            columnspan=2,
            padx=(SCALE_FACTOR, SCALE_FACTOR),
            pady=(SCALE_FACTOR, 0),
            sticky="ew",
        )

        output_entry = CTkEntry(ctk, state="readonly", textvariable=self._directory)
        output_entry.grid(
            row=3,
            column=0,
            padx=(SCALE_FACTOR, SCALE_FACTOR),
            pady=(SCALE_FACTOR, 0),
            sticky="ew",
        )

        select_dir_button = CTkButton(
            ctk, text="📁", width=40, command=self._change_directory
        )
        select_dir_button.grid(
            row=3,
            column=1,
            padx=(0, SCALE_FACTOR),
            pady=(SCALE_FACTOR, 0),
            sticky="ew",
        )

        create_report_button = CTkButton(
            ctk, text="Создать отчет", command=self._build_report
        )
        create_report_button.grid(
            row=4,
            column=0,
            columnspan=2,
            padx=(SCALE_FACTOR, SCALE_FACTOR),
            pady=(2 * SCALE_FACTOR, 0),
            sticky="ew",
        )

        self._clickable.extend(
            [course_entry, output_entry, select_dir_button, create_report_button]
        )

    def _change_directory(self) -> None:
        result = filedialog.askdirectory(
            initialdir=self._directory.get(),
            mustexist=True,
            title="Выберите директорию для сохранения отчета",
        )

        if result:
            self._directory.set(result)

    def _build_report(self) -> None:
        async def _internal_build_report() -> None:
            course_id = self._course_id.get()
            if not course_id:
                show_error(self._ctk, "Отсутствует ссылка на курс или идентификатор")
                return

            if not self._cached_session:
                show_error(
                    self._ctk,
                    "Не удалось получить сессию. Выполните повторный вход для продолжения.",
                )
                self._ensure_session_init()
                return

            try:
                await build_report(
                    self._cached_session,
                    course_id,
                    lambda size: ProgressHandlerContext(self._ctk, size),
                    self._directory.get(),
                )

                show_information(self._ctk, "Отчет успешно загружен.")
            except Exception as e:
                show_error(
                    self._ctk,
                    f"Произошла непредвиденная ошибка. {e!s} Повторите попытку позднее.",
                )

        with DisabledContext(self._clickable):
            run(_internal_build_report())

    def _init_session(self) -> None:
        async def _get_valid_cached_session(
            login: str | None,
        ) -> MoodleCachedSession | None:
            while True:
                credentials = LoginDialog(self._ctk, login).credentials
                if not credentials:
                    return None

                login = credentials.login
                try:
                    session = await authorize(credentials)
                except Exception:
                    show_error(
                        self._ctk, "Некорректный логин или пароль. Попробуйте снова."
                    )
                    continue

                try:
                    await serialize_session(SESSION_FILE, session)
                except Exception:
                    show_warning(
                        self._ctk,
                        "Не удалось сохранить сессию в файл. Понадобится повторная авторизация после перезапуска приложения.",
                    )

                return session

        async def _internal_init_session() -> None:
            try:
                cached_session = await restore_session(SESSION_FILE)
            except Exception:
                # Session is corrupted or isn't created. Show the login page without login value.
                self._cached_session = await _get_valid_cached_session(login=None)
                return

            async with MoodleSession(cached_session) as session:
                if not await session.is_valid():
                    show_warning(
                        self._ctk,
                        "Сессия просрочена. Выполните повторный вход для продолжения.",
                    )

                    # Remove expired session file
                    with suppress(OSError):
                        os.remove(SESSION_FILE)

                    # Session expired. Show the login page with previous login value.
                    self._cached_session = await _get_valid_cached_session(
                        login=cached_session.login
                    )
                    return

            self._cached_session = cached_session

        run(_internal_init_session())

    def _ensure_session_init(self) -> None:
        if not self._cached_session:
            self._is_destroyed = True
            self._ctk.destroy()


def show_information(master: Any, message: str) -> None:
    """Show an information message dialog.

    Args:
        master (Any): The parent window.
        message (str): The message to display.
    """

    dialog = CTkMessagebox(
        master,
        title="Информация",
        message=message,
    )
    master.wait_window(dialog)


def show_warning(master: Any, message: str) -> None:
    """Show a warning message dialog.

    Args:
        master (Any): The parent window.
        message (str): The message to display.
    """

    dialog = CTkMessagebox(
        master,
        title="Предупреждение",
        message=message,
        icon="warning",
    )
    master.wait_window(dialog)


def show_error(master: Any, message: str) -> None:
    """Show an error message dialog.

    Args:
        master (Any): The parent window.
        message (str): The message to display.
    """

    dialog = CTkMessagebox(
        master,
        title="Ошибка",
        message=message,
        icon="cancel",
    )
    master.wait_window(dialog)
