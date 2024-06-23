from logic.serialization import deserialize_report, serialize_report_to_excel
from moodle.auth import MoodleCachedSession
from moodle.models import ChoiceMoodleSection
from moodle.session import MoodleSession
from os import path


async def build_report(cached_session: MoodleCachedSession, course_id: str | int, output_directory: str = '.') -> None:
    '''Generate a report for a specific Moodle course and save it as an Excel file.

    Args:
        cached_session (MoodleCachedSession): The cached Moodle session used to authenticate.
        course_id (str | int): The ID or URL of the course to generate the report for.
        output_directory (str, optional): The directory where the report will be saved. Defaults to the current directory.
    '''

    async with MoodleSession(cached_session) as session:
        course = await session.get_course(course_id)

        for section in course.sections:
            if not isinstance(section, ChoiceMoodleSection):
                continue

            report = await session.get_excel_report(section.id)
            report = deserialize_report(report)

            filename = path.join(output_directory, f'{course.name}.xsls')
            await serialize_report_to_excel(filename, report)
