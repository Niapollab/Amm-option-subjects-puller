from logic.serialization import deserialize_report, serialize_report_to_excel
from moodle.auth import MoodleCachedSession
from moodle.models import ChoiceMoodleActivity
from moodle.progress import ProgressHandler, ProgressHandlerFactory, Bar
from moodle.session import MoodleSession
from customtkinter import CTk
from os import path


async def build_report(
    cached_session: MoodleCachedSession,
    course_id: str | int,
    progress_factory: ProgressHandlerFactory[int] | None = None,
    output_directory: str = ".",
    root: CTk | None = None

) -> None:
    """Generate a report for a specific Moodle course and save it as an Excel file.

    Args:
        cached_session (MoodleCachedSession): The cached Moodle session used to authenticate.
        course_id (str | int): The ID or URL of the course to generate the report for.
        progress_factory (ProgressHandlerFactory[int], optional): progress_factory (ProgressHandlerFactory[int], optional): A factory to create a progress handler to track the report generation progress. Defaults to None.
        output_directory (str, optional): The directory where the report will be saved. Defaults to the current directory.
    """

    async with MoodleSession(cached_session) as session:
        course = await session.get_course(course_id)
        activities_count = sum(
            1
            for section in course.sections
            for activity in section.activities
            if isinstance(activity, ChoiceMoodleActivity)
        )
        progress_factory = progress_factory or ProgressHandler.mock
        count = 0
        with progress_factory(Bar, activities_count) as progress:
            progress.prepare_bar(root)
            for section in course.sections:
                for activity in section.activities:
                    if not isinstance(activity, ChoiceMoodleActivity):
                        continue
                    report = await session.get_excel_report(activity.id)
                    report = deserialize_report(report)
                    filename = f"{course.name}-{section.name}-{activity.name}.xlsx"
                    filename = path.join(output_directory, filename)

                    serialize_report_to_excel(filename, report)
                    count+=1
                    progress.update(count)
