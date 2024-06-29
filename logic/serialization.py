from logic.models import Report
from logic.models import Identificator, Student
import pandas as pd

def deserialize_report(df_report: pd.DataFrame) -> Report:
    '''Convert a DataFrame into a Report object.

    Args:
        df_report (pd.DataFrame): The DataFrame containing the report data.

    Returns:
        Report: A Report object with parsed student group numbers and student data.
    '''
    try:
        student_map=dict()
        for _,row in df_report.iterrows():
            last_name=row['Фамилия']
            first_name=row['Имя']
            identificator=Identificator.from_str(row['Группа'])
            group=identificator.group
            choice=row['Вариант ответа']
            student = Student(f'{last_name} {first_name}', choice)
            if group in student_map:
                student_map[group].append(student)
            else:
                student_map[group] = [student]
    except KeyError as e:
        print(f"Probably invalid dataframe column name {e}")
    except Exception as e:
        print(f"Error of creating report: {e}")
    return Report(student_map)

async def serialize_report_to_excel(filename: str, report: Report) -> None:
    '''Serialize a Report object into an Excel file.

    Args:
        filename (str): The path to the file where the report will be saved.
        report (Report): The Report object containing the data to be serialized.
    '''

    ...
