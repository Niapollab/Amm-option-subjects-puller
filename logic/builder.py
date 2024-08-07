from logic.serialization import deserialize_report, serialize_report_to_excel
from moodle.auth import MoodleCachedSession
from moodle.models import ChoiceMoodleActivity
from moodle.progress import ProgressHandler, ProgressHandlerFactory
from moodle.session import MoodleSession
from os import path
import asyncio


async def build_report(
    cached_session: MoodleCachedSession,
    course_id: str | int,
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
        course = await session.get_course(course_id)
        activities_count = sum(
            1
            for section in course.sections
            for activity in section.activities
            if isinstance(activity, ChoiceMoodleActivity)
        )

        report_tasks = []
        for section in course.sections:
            for activity in section.activities:
                if not isinstance(activity, ChoiceMoodleActivity):
                    continue

                report_tasks.append(
                    (
                        course.name,
                        section.name,
                        activity.name,
                        asyncio.create_task(session.get_excel_report(activity.id)),
                    )
                )

        progress_factory = progress_factory or ProgressHandler.mock
        count = 0
        with progress_factory(activities_count) as progress:
            for course_name, section_name, activity_name, task in report_tasks:
                report = await task
                report = deserialize_report(report)

                filename = f"{course_name}-{section_name}-{activity_name}.xlsx"
                filename = path.join(output_directory, filename)

                serialize_report_to_excel(filename, report)
                count += 1
                progress.update(count)
