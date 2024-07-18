from typing import Any, Iterable
from logic.exceptions import SerializeReportError
from logic.models import Report, Student
import pandas as pd


def serialize_report_to_excel(filename: str, report: Report) -> None:
    """Serialize a Report object into an Excel file.

    Args:
        filename (str): The path to the file where the report will be saved.
        report (Report): The Report object containing the data to be serialized.
    """

    with pd.ExcelWriter(filename, engine="openpyxl", mode="w") as writer:
        try:
            rows = __enumerate_df_rows(report.students)
            df = pd.DataFrame(rows)

            df = df.sort_values(by="ФИО")
            df.to_excel(writer, index=False)

            *_, worksheet = next(iter(writer.sheets.items()))
            _auto_adjust_column_width(worksheet)
        except Exception as e:
            raise SerializeReportError(f'Error of creating report "{e}".')


def __enumerate_df_rows(students: Iterable[Student]) -> Iterable[dict[str, Any]]:
    for student in students:
        priority = {
            priority: index for index, priority in enumerate(student.priority, 1)
        }

        row = {"ФИО": student.fullname, "Договор": "", **priority, "Баллы": ""}
        yield row


def _auto_adjust_column_width(worksheet: Any) -> None:
    ADDITIONAL_SPACE = 2
    for col in worksheet.columns:
        max_length = 0
        column = col[0].column_letter

        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except Exception:
                pass

        adjusted_width = max_length + ADDITIONAL_SPACE
        worksheet.column_dimensions[column].width = adjusted_width
