import openpyxl

def parse_excel_and_extract_questions(excel_file):
    # Load the Excel file
    wb = openpyxl.load_workbook(excel_file)
    sheet = wb.active
    
    questions = []
    
    # Assuming the structure of the Excel file:
    # Column A: Question
    # Column B: Option 1
    # Column C: Option 2
    # Column D: Option 3
    # Column E: Option 4
    # Column F: Correct Answer
    for row in sheet.iter_rows(min_row=2, values_only=True):
        question = {
            'question': row[0],
            'option1': row[1],
            'option2': row[2],
            'option3': row[3],
            'option4': row[4],
            'answer': row[5],
            'marks':row[6]
        }
        questions.append(question)
    
    return questions
