from collections import defaultdict
from logic.exceptions import DeserializeReportError, InvalidColumnNameError
from logic.models import Identificator, Student
from logic.models import Report
import pandas as pd


def deserialize_report(df_report: pd.DataFrame) -> Report:
    """Convert a DataFrame into a Report object.

    Args:
        df_report (pd.DataFrame): The DataFrame containing the report data.

    Returns:
        Report: A Report object with parsed student group numbers and student data.
    """

    try:
        student_map = defaultdict(list)
        for _, row in df_report.iterrows():
            last_name = row["Фамилия"]
            first_name = row["Имя"]
            identificator = Identificator.from_str(row["Группа"])
            group = identificator.group
            choice = row["Вариант ответа"]
            student = Student(f"{last_name} {first_name}", choice)
            student_map[group].append(student)
    except KeyError as e:
        raise InvalidColumnNameError(f'Invalid dataframe column name "{e}".')
    except Exception as e:
        raise DeserializeReportError(f'Error of creating report "{e}".')

    return Report(student_map)

def auto_adjust_column_width(ws):
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter 
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

async def serialize_report_to_excel(filename: str, report: Report) -> None:
    """Serialize a Report object into an Excel file.

    Args:
        filename (str): The path to the file where the report will be saved.
        report (Report): The Report object containing the data to be serialized.
    """
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        for group, students in report.groups.items():
            df = pd.DataFrame([{"ФИО": student.fullname, "Предмет": student.subject} for student in students])
            df = df.sort_values(by="ФИО")
            df.to_excel(writer, sheet_name=str(group), index=False)
            
            worksheet = writer.sheets[str(group)]
            auto_adjust_column_width(worksheet)
