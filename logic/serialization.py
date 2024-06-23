from logic.models import Report
import pandas as pd


def deserialize_report(df_report: pd.DataFrame) -> Report:
    '''Convert a DataFrame into a Report object.

    Args:
        df_report (pd.DataFrame): The DataFrame containing the report data.

    Returns:
        Report: A Report object with parsed student group numbers and student data.
    '''

    # TODO: Use `Identificator` to parse student group number

    ...


async def serialize_report_to_excel(filename: str, report: Report) -> None:
    '''Serialize a Report object into an Excel file.

    Args:
        filename (str): The path to the file where the report will be saved.
        report (Report): The Report object containing the data to be serialized.
    '''

    ...
