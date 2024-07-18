from os import path
from logic.serialization import serialize_report_to_excel
from moodle.auth import MoodleCachedSession
from moodle.progress import ProgressHandlerFactory
from logic.session import MoodleSession


async def build_report(
    cached_session: MoodleCachedSession,
    quiz_id: str | int,
    progress_factory: ProgressHandlerFactory[int] | None = None,
    output_directory: str = ".",
) -> None:
    """Generate a report for a specific Moodle course and save it as an Excel file.

    Args:
        cached_session (MoodleCachedSession): The cached Moodle session used to authenticate.
        course_id (str | int): The ID or URL of the course to generate the report for.
        progress_factory (ProgressHandlerFactory[int], optional): progress_factory (ProgressHandlerFactory[int], optional): A factory to create a progress handler to track the report generation progress. Defaults to None.
        output_directory (str, optional): The directory where the report will be saved. Defaults to the current directory.
    """

    async with MoodleSession(cached_session) as session:
        report = await session.get_quiz_report(quiz_id, progress_factory)
        filename = path.join(output_directory, "Отчет о приоритетах кафедр ПМИ.xlsx")

        serialize_report_to_excel(filename, report)
