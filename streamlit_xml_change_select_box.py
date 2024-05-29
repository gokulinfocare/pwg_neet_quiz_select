# This program uses XML data and use streamlit to update the data and then generate a new XML file
# Have to change the path mentioned for saving updated XML file
import streamlit as st 
import xml.etree.ElementTree as ET
import sys
import pandas as pd
import base64
import pyodbc
from datetime import datetime
import os
#from time import sleep

from function_moodle_xml_create import create_moodle_xml
global col_counter
col_counter = 0
def aws_start_connection():
    try:
        conn = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};"
                "Server=pwgdb.c3we26w6ytfr.ap-southeast-2.rds.amazonaws.com;"
                "Database=RamaKrishna;"
                "uid=admin;pwd=PwgAws99"
                )
        cursor = conn.cursor()

    except pyodbc.Error as e:
        error_found = "true"       
        print(f"An error occurred connecting to AWS database : {e}")
        sys.exit()

    return conn, cursor


# Function to get data from XML file
def get_data_from_xml():

    xml_table = []              # List to store the data from XML file
    new_filename = "updated.xml"   # Default name for updated XML file
    
    #st.set_page_config(page_title="Please upload XML file to display/edit the data", layout="wide")
    
    file_name = st.file_uploader("Choose the XML file you want to display/edit")
    if file_name is not None:
        new_filename = file_name.name[:-4] + "updated.xml"
        file_contents = file_name.read().decode("utf-8")
        root = ET.fromstring(file_contents)
        xml_table = []
        #Takes data from the XML file uploaded and stores it in a list of dictionaries
        for element in root.findall('.//question'):
            if element.attrib['type'] == 'multichoice':
                moodle_id = qtext = soln = option1 = option2 = option3 = option4 = answer = ''     
                moodle_id = element.find('.//name/text').text
                qtext = element.find('.//questiontext/text').text                
                if 'Question ID' in qtext:
                    w_question_id = qtext.split('<br>')[0]
                soln = element.find('.//correctfeedback/text').text
                w_count = 1
                w_incorrect_feedback = ""
                xml_feedback = ""
                for rec in element.findall('.//answer'):
                    if w_incorrect_feedback == "":
                        if rec.find('feedback/text') is not None:
                            xml_feedback = rec.find('feedback/text').text
                        if xml_feedback is not None:
                            w_incorrect_feedback = xml_feedback
                    if w_count == 1:
                        option1 = rec.find('text').text
                        if rec.attrib['fraction'] == '100':
                            answer = 'A'
                    elif w_count == 2:
                        option2 = rec.find('text').text
                        if rec.attrib['fraction'] == '100':
                            answer = 'B'
                    elif w_count == 3:
                        option3 = rec.find('text').text
                        if rec.attrib['fraction'] == '100':
                            answer = 'C'
                    elif w_count == 4:
                        option4 = rec.find('text').text
                        if rec.attrib['fraction'] == '100':
                            answer = 'D'
                    w_count += 1
                qtext = qtext.replace('<br>', '\n')
                option1 = option1.replace('<br>', '\n')
                option2 = option2.replace('<br>', '\n')
                option3 = option3.replace('<br>', '\n')
                option4 = option4.replace('<br>', '\n')
                soln = soln.replace('<br>', '\n')
                w_incorrect_feedback = w_incorrect_feedback.replace('<br>', '\n')
                struc = {
                    'moodle_id': moodle_id,
                    'questiontext': qtext,                    
                    'option1': option1,
                    'option2': option2,
                    'option3': option3,
                    'option4': option4,
                    'answer': answer,
                    'soln': soln,
                    'incorrect_feedback': w_incorrect_feedback,
                    'question_id': w_question_id
                }
                xml_table.append(struc)
        # Get the filename from the file_uploader widget
        filename = file_name.name
        
        # Get the file extension
        file_extension = filename.split(".")[-1]
        
        # Create the new filename with "_updated.xml" suffix
        new_filename = filename.replace(f".{file_extension}", "_updated.xml")
        
        # Check if the number of records is 50
        if len(xml_table) != 50:
            print("50 records not found in XML file")
            sys.exit()
        
    return xml_table , new_filename         # Return the data and new filename

# Function to display original data 
def display_data(data):
    st.write("### Original Data:")
    st.dataframe(data)

# Function to edit data
def edit_data(data):
    st.write("### Edit Data:")
    num_rows = len(data)

    # Get column names from the keys of the first dictionary in the list
    if num_rows > 0:
        column_names = list(data[0].keys())
    else:
        column_names = []

    # Create empty DataFrame with columns
    edited_data = pd.DataFrame(columns=column_names, index=range(num_rows))
    w_count = 0
    w_en_lang = ""
    if data[0]['questiontext'].isascii():
        w_en_lang = "X"
    for rec in data:
        #w_count += 1
        if 'question_id' in rec:            
            st.write(f":blue[{rec['question_id']}]")            
            #st.write(question_id)        
        for key in rec.keys():
            if key == 'moodle_id' or key == 'question_id' :
                edited_data.at[w_count, key] = rec[key]                
                continue
            if w_en_lang == "X" and key == 'incorrect_feedback':
                edited_data.at[w_count, key] = rec[key]                
                continue
            if "\\(" in rec[key] or "\\[" in rec[key]:
                if "\\)\\(" in rec[key]:
                    rec[key] = rec[key].replace("\\)\\(", "\\) \\(")
                if "\\]\\[" in rec[key]:
                    rec[key] = rec[key].replace("\\]\\[", "\\] \\[")
                w_latex = rec[key]
                w_latex = w_latex.replace('\\(', "$").replace('\\)', "$").replace('\\[', "$$").replace('\\]', "$$")
                st.markdown(w_latex)
            if len(rec[key]) > 180 :
                edited_data.at[w_count, key] = st.text_area(f"Row {w_count} - {key}", rec[key],  height=125)
            elif '\n' in rec[key]:
                edited_data.at[w_count, key] = st.text_area(f"Row {w_count} - {key}", rec[key],  height=30)
            else:
                edited_data.at[w_count, key] = st.text_input(f"Row {w_count} - {key}", rec[key])
        w_count += 1
        st.divider()
    # data = pd.DataFrame(data)           #Convert the list of original data to a dataframe
    # for i in range(len(data)):
    #     for col in data.columns:
    #         if "\(" in data.at[i, col]:
    #             w_latex = data.at[i, col]
    #             w_latex = w_latex.replace('\(', "")
    #             w_latex = w_latex.replace('\)', "")                          
    #             st.latex(w_latex)
    #         if col == 'moodle_id':
    #             edited_data.at[i, col] = data.at[i, col]
    #             st.write('Question ID: ' + )
    #             #st.write(f"### {col}: {data.at[i, col]}")
    #             continue
    #         if len(data.at[i, col]) > 180:     #If the length of the data is more than 180 chars
    #             edited_data.at[i, col] = st.text_area(f"Row {i+1} - {col}", data.at[i, col],  height=125)
    #         else:
    #             edited_data.at[i, col] = st.text_input(f"Row {i+1} - {col}", data.at[i, col])   #Edits the data in the dataframe
    return edited_data

def create_xml_file(subject, language, quiz_no):

    # Make sure all the records are verified before creating the XML file
    w_connection = aws_start_connection()
    conn = w_connection[0]
    cursor = w_connection[1]
    language = language[:2]
    moodle_id_like = 'IN' + subject[0] + '%'
    quiz_no = int(quiz_no)
    try:
            
        cursor.execute("SELECT * FROM AWS_MOODLE_QUESTIONS WHERE language = ? AND moodle_id LIKE ? and quiz_no = ? and verifier_1 is NOT Null", (language, moodle_id_like, quiz_no,))
        #cursor.execute("SELECT * FROM AWS_MOODLE_QUESTIONS WHERE language = ? AND moodle_id LIKE ? and quiz_no = ? ", (language, moodle_id_like, quiz_no, ))
    
        columns = [column[0] for column in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, row)))
    except pyodbc.Error as e:
        error_found = "true"       
        st.sidebar.error(f"An error occurred connecting to AWS database : {e}")
        sys.exit()

    if len(rows) == 0:
        st.sidebar.error("No records found in the database for the selected subject and language")
        sys.exit()
    elif len(rows) != 50:
        st.sidebar.error("All records are NOT verified. Please verify all records before creating the XML file")
        sys.exit()
    else:
        #st.sidebar.write("### All records are verified. Please click below button to create the XML file")
        now = datetime.now()
        date_time_str = now.strftime("%Y%m%d_%H%M%S")
        lang = 'EN'
        subject_desc = subject.split('-')[1]
        subject_desc = subject_desc.strip()
        xml_file_name = f"{subject_desc}_Quiz#{str(quiz_no)}_{date_time_str}_{lang}_updated.xml"
        xml_modified_data = create_moodle_xml(rows)
        xml_data_utf8 = xml_modified_data.encode('utf-8')
        st.sidebar.subheader("XML file has been created successfully!. Please click below button to download")
        st.sidebar.download_button(
            label=" Click to Download XML File",
            data=xml_data_utf8,
            file_name=xml_file_name,
            mime="application/xml",
            key = "download_button"
            )
        download_js = f"""
        <script>
        const blob = new Blob(["{xml_data_utf8}"], {{ type: "application/xml" }});
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = '{xml_file_name}';
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
        URL.revokeObjectURL(url);
        </script>
        """
        st.markdown(download_js, unsafe_allow_html=True)


    

def create_xml(input_table,new_filename):
    return
    if st.button("Please check and confirm the above changes"):
        #input_table = data.to_dict('records')
        output_table = []
        for data in input_table:        
            data['questiontext'] = data['questiontext'].replace('\n', '<br>')
            data['option1'] = data['option1'].replace('\n', '<br>')
            data['option2'] = data['option2'].replace('\n', '<br>')
            data['option3'] = data['option3'].replace('\n', '<br>')
            data['option4'] = data['option4'].replace('\n', '<br>')
            data['soln'] = data['soln'].replace('\n', '<br>')
            data['incorrect_feedback'] = data['incorrect_feedback'].replace('\n', '<br>')
            output_table.append(data)

        # Remove the below code
        # test_table = []
        # for rec in output_table:
        #     if 'B10261' in rec['questiontext']:
        #         st.subheader(rec['soln'])
        #         test_table.append(rec)
        #         break
        # output_table = test_table
        # Remove the above code         

        xml_modified_data = create_moodle_xml(output_table)
        xml_data_utf8 = xml_modified_data.encode('utf-8')
        st.subheader("XML file has been created successfully!. Please click below button to download")
        st.download_button(
            label=" Click to Download XML File",
            data=xml_data_utf8,
            file_name=new_filename,
            mime="application/xml",
            key = "download_button"
            )
        
        # Add JavaScript to trigger download of the file
        # Add JavaScript to trigger download of the file
        # Add JavaScript to trigger download of the file
        # download_js = f"""
        # <script>
        # const blob = new Blob(["{xml_data_utf8}"], {{ type: "application/xml" }});
        # const url = URL.createObjectURL(blob);
        # const anchor = document.createElement('a');
        # anchor.href = url;
        # anchor.download = '{new_filename}';
        # document.body.appendChild(anchor);
        # anchor.click();
        # document.body.removeChild(anchor);
        # URL.revokeObjectURL(url);
        # </script>
        # """
        # st.markdown(download_js, unsafe_allow_html=True)
    #b64_encoded_xml = base64.b64encode(xml_tree.encode()).decode()
    #tree = f'<a href="data:application/xml;base64,{b64_encoded_xml}">Download XML</a>'
    #download_link = st.download_button("Save Changes and Download XML File", tree, file_name=new_filename, mime="application/xml")
    #Write the ElementTree object to an XML file mentioning path name
    #file_path = f"C:/Users/Taanya/Desktop/AssignGokul/Streamlit/{new_filename}"
    # file_path = f"C:/Moodle Files/Languages/{new_filename}"
    # with open(file_path, 'w', encoding='utf-8') as file:
    #     file.write(tree)
    #xml_string = ET.tostring(tree, encoding="utf-8")    
    #st.download_button(label="Save Changes and Download XML File ", data=tree, file_name=new_filename)

    #st.write("### Updated XML file has been created successfully!")


# def compare_original_and_updated_data(xml_table, updated_data):
#     user_data = updated_data.to_dict('records')
#     st.write("### Updated Data:")
#     w_count = 0
#     w_changed = ""
#     output = []
#     for rec in xml_table:
#         for user_rec in user_data:
#             if rec['moodle_id'] != user_rec['moodle_id']:
#                 continue
#             w_changed = ""
#             # Replace space begin and end of the string
#             rec['questiontext'] = rec['questiontext'].strip()
#             rec['option1'] = rec['option1'].strip()
#             rec['option2'] = rec['option2'].strip()
#             rec['option3'] = rec['option3'].strip()
#             rec['option4'] = rec['option4'].strip()
#             rec['answer'] = rec['answer'].strip()
#             rec['soln'] = rec['soln'].strip()
#             # if rec['soln'][-1] != '.':
#             #         rec['soln'] = user_rec['soln'] + '.'
#             rec['incorrect_feedback'] = rec['incorrect_feedback'].strip()
#             if 'question_id' in rec:
#                 w_question_id = rec['question_id']
#             else:  
#                 w_question_id = rec['moodle_id']
#         #for user_rec in user_data:
#             # Replace space begin and end of the string
#             user_rec['questiontext'] = user_rec['questiontext'].strip()
#             user_rec['option1'] = user_rec['option1'].strip()
#             user_rec['option2'] = user_rec['option2'].strip()
#             user_rec['option3'] = user_rec['option3'].strip()
#             user_rec['option4'] = user_rec['option4'].strip()
#             user_rec['answer'] = user_rec['answer'].strip()
#             user_rec['soln'] = user_rec['soln'].strip()
#             if user_rec['soln'][-1] != '.':
#                 user_rec['soln'] = user_rec['soln'] + '.'
#             user_rec['incorrect_feedback'] = user_rec['incorrect_feedback'].strip()
            
#             if rec['moodle_id'] == user_rec['moodle_id']:
#                 if rec['questiontext'] != user_rec['questiontext']:
#                     if w_changed == "":
#                         st.write(f":blue[Below Changes were done for {w_question_id}]")
#                     st.write(f":red[Original Question Text : ]" + rec['questiontext'])
#                     st.write(f':green[Updated Question Text : ]' + user_rec['questiontext'])
#                     w_changed = "X"
#                 if rec['option1'] != user_rec['option1']:
#                     if w_changed == "":
#                         st.write(f":blue[Below Changes were done for {w_question_id}]")
#                     st.write(f':red[Original Option 1 : ]' + rec['option1'])
#                     st.write(f':green[Updated Option 1 : ]' + user_rec['option1'])
#                     w_changed = "X"
#                 if rec['option2'] != user_rec['option2']:
#                     if w_changed == "":
#                         st.write(f":blue[Below Changes were done for {w_question_id}]")
#                     st.write(f':red[Original Option 2 : ]' + rec['option2'])
#                     st.write(f':green[Updated Option 2 : ]' + user_rec['option2'])
#                     w_changed = "X"
#                 if rec['option3'] != user_rec['option3']:
#                     if w_changed == "":
#                         st.write(f":blue[Below Changes were done for {w_question_id}]")
#                     st.write(f':red[Original Option 3 : ]' + rec['option3'])
#                     st.write(f':green[Updated Option 3 : ]' + user_rec['option3'])
#                     w_changed = "X"
#                 if rec['option4'] != user_rec['option4']:
#                     if w_changed == "":
#                         st.write(f":blue[Below Changes were done for {w_question_id}]")
#                     st.write(f':red[Original Option 4 : ]' + rec['option4'])
#                     st.write(f':green[Updated Option 4 : ]' + user_rec['option4'])
#                     w_changed = "X"
#                 if rec['answer'] != user_rec['answer']:
#                     if w_changed == "":
#                         st.write(f":blue[Below Changes were done for {w_question_id}]")
#                     st.write(f':red[Original Answer : ]' + rec['answer'])
#                     st.write(f':green[Updated Answer : ]' + user_rec['answer'])
#                     w_changed = "X" 
#                 if rec['soln'] != user_rec['soln']:
#                     if w_changed == "":
#                         st.write(f":blue[Below Changes were done for {w_question_id}]")
#                     st.write(f':red[Original Solution : ]' + rec['soln'])
#                     st.write(f':green[Updated Solution : ]' + user_rec['soln'])
#                     w_changed = "X"
#                 if rec['incorrect_feedback'] != user_rec['incorrect_feedback']:
#                     if w_changed == "":
#                         st.write(f":blue[Below Changes were done for {w_question_id}]")
#                     st.write(f':red[Original Incorrect Feedback : ]' + rec['incorrect_feedback'])
#                     st.write(f':green[Updated Incorrect Feedback : ]' + user_rec['incorrect_feedback'])
#                     w_changed = "X"
                
#                 if w_changed == "X":
#                     w_count += 1
#                     st.divider()
#             struc = {
#                 'moodle_id': user_rec['moodle_id'],
#                 'questiontext': user_rec['questiontext'],
#                 'option1': user_rec['option1'],
#                 'option2': user_rec['option2'],
#                 'option3': user_rec['option3'],
#                 'option4': user_rec['option4'],
#                 'answer': user_rec['answer'],
#                 'soln': user_rec['soln'],
#                 'incorrect_feedback': user_rec['incorrect_feedback']                
#             }
#             output.append(struc)        
                
#     if w_count == 0:
#         st.write("No changes found in the data")
#     else:
#         st.subheader(f"Total {w_count} records have been changed")
#         #output.append('X')           
                
                
#                 # if rec['questiontext'] != user_rec['questiontext'] or rec['option1'] != user_rec['option1'] or rec['option2'] != user_rec['option2'] or rec['option3'] != user_rec['option3'] or rec['option4'] != user_rec['option4'] or rec['soln'] != user_rec['soln'] or rec['incorrect_feedback'] != user_rec['incorrect_feedback']:
#                 #    output.append(user_rec)

#     return output, w_count

def get_subject_options(input_text):

    #st.set_page_config(page_title="Update Quiz Data", layout="wide")  
    output_table = []
    
    output_table.append(input_text)
    output_table.append("PH - Physics")
    output_table.append("CH - Chemistry")
    output_table.append("BI - Biology")

    return output_table

def get_language_options():
    output_table = []
    output_table.append("EN - English")
    output_table.append("AS - Assamese")
    output_table.append("BN - Bengali")
    output_table.append("GU - Gujarati")
    output_table.append("HI - Hindi")
    output_table.append("KN - Kannada")
    output_table.append("ML - Malayalam")
    output_table.append("MR - Marathi")
    output_table.append("OR - Oriya")
    output_table.append("PA - Punjabi")
    output_table.append("TA - Tamil")
    output_table.append("TE - Telugu")
    output_table.append("UR - Urdu")

    return output_table

def get_quiz_no_table(subject, lang, quiz_no_msg):
    output_table = []
    w_connection = aws_start_connection()
    conn = w_connection[0]
    cursor = w_connection[1]
    language = lang[:2]
    moodle_id_like = 'IN' + subject[0] + '%'
    try:
        
        cursor.execute("SELECT DISTINCT quiz_no FROM AWS_MOODLE_QUESTIONS WHERE language = ? AND moodle_id LIKE ? ", (language, moodle_id_like, ))
       
        columns = [column[0] for column in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, row)))
    except pyodbc.Error as e:
        error_found = "true"       
        st.error(f"An error occurred connecting to AWS database : {e}")
        sys.exit()

    if rows == []:
        st.error("No records found in the database for the selected subject and language")
    else:
        output_table.append(quiz_no_msg)
        for row in rows:
            output_table.append(row['quiz_no'])
    conn.close()
    return output_table
    
def get_quiz_no_data(subject, lang, quiz_no):
    
    qno_table = []
    w_connection = aws_start_connection()
    conn = w_connection[0]
    cursor = w_connection[1]
    language = lang[:2]
    moodle_id_like = 'IN' + subject[0] + '%'    
    quiz_no = int(quiz_no)
    try:
        
        cursor.execute("SELECT * FROM AWS_MOODLE_QUESTIONS WHERE language = ? AND moodle_id LIKE ? and quiz_no = ?", (language, moodle_id_like, quiz_no))
       
        columns = [column[0] for column in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, row)))
    except pyodbc.Error as e:
        error_found = "true"       
        st.error(f"An error occurred connecting to AWS database : {e}")
        sys.exit()

    if rows == []:
        st.error("No records found in the database for the selected subject and language")
    else:
        w_count = 0
        for rec in rows:
            w_count += 1
            # struc = {
            #     'record_key': w_count,
            #     'language': rec['language'],
            #     'moodle_id': rec['moodle_id'],
            #     'moodle_qno': rec['moodle_qno'],
            #     # 'questiontext': rec['questiontext'],
            #     # 'option1': rec['option1'],
            #     # 'option2': rec['option2'],
            #     # 'option3': rec['option3'],
            #     # 'option4': rec['option4'],
            #     # 'answer': rec['answer'],
            #     # 'soln': rec['soln'],
            #     # 'incorrect_feedback': rec['incorrect_feedback'],
            #     # 'status': rec['status'],
            #     # 'verifier_1': rec['verifier_1'],
            #     # 'verifier1_date': rec['verifier1_date'],
            #     # 'verifier_2': rec['verifier_2'],
            #     # 'verifier2_date': rec['verifier2_date']
            # }        
            # output_table.append(struc)
            w_qno_rec = str(w_count) + '-' + subject[0] + str(rec['moodle_qno'])
            qno_table.append(w_qno_rec)
    conn.close()
    return qno_table

def get_current_record(subject, lang, quiz_no, question_id):

    w_connection = aws_start_connection()
    conn = w_connection[0]
    cursor = w_connection[1]
    moodle_id_like = 'IN' + subject[0] + '%'
    language = lang[:2]
    quiz_no = int(quiz_no)
    moodle_qno = question_id[1:]
    moodle_qno = int(moodle_qno)
    try:
        
        cursor.execute("SELECT * FROM AWS_MOODLE_QUESTIONS WHERE language = ? and moodle_id like ? and moodle_qno = ? and quiz_no = ?", (language, moodle_id_like, moodle_qno, quiz_no ))
       
        columns = [column[0] for column in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, row)))
    except pyodbc.Error as e:
        error_found = "true"       
        st.error(f"An error occurred connecting to AWS database : {e}")
        sys.exit()

    if rows == []:
        st.error("No records found in the database for the selected subject and language")
        
    conn.close()

    return rows[0]

def format_latex(input_text):

    output_text = input_text
    latex_ind = ""
    if "\\(" in output_text or "\\[" in output_text:
        if "\\)\\(" in output_text:
            output_text = output_text.replace("\\)\\(", "\\) \\(")
        if "\\]\\[" in output_text:
            output_text = output_text.replace("\\]\\[", "\\] \\[")
        w_latex = output_text
        w_latex = w_latex.replace('\\(', "$").replace('\\)', "$").replace('\\[', "$$").replace('\\]', "$$")
        latex_ind = "X"
        

    return w_latex, latex_ind

def text_field(lable_text, input_text, **input_params):
    global col_counter
    
    col_counter += 1    
    w_column1 = 'col' + str(col_counter)
    col_counter += 1
    w_column2 = 'col' + str(col_counter)

    
    display_text, latex_ind = format_latex(input_text)
    output_text = ""

    
    # if latex_ind == "X":
    #    output_text = st.latex(display_text)
    # else:
    #     if len(display_text) > 180 :                
    #         output_text = st.text_area(lable_text, display_text,   height=125)
    #     else: 
    #         output_text = st.text_input(lable_text, display_text )
    # Define the first row with label and text input
    params = {}
    params.setdefault('label_visibility', 'collapsed')  
    w_column1, w_column2 = st.columns([2, 18])
    with w_column1:        
        st.write(lable_text)
    with w_column2:                
        if latex_ind == "X":
            st.markdown(display_text)            
            #output_text = st.latex(display_text)
        else:
            if len(display_text) > 180 :                
                output_text = st.text_area("", input_text,   height=125, **params)
            else: 
                output_text = st.text_input("", input_text, **params)
    
    return output_text

def edit_current_record(rec):
    # Custom CSS to reduce space between the rows
    st.markdown(
        """
        <style>
        .label-row {
            display: flex;
            align-items: center;
            margin-bottom: 0rem; /* Adjust as needed */
        }
        .label {
            margin-right: 10px;
            min-width: 80px; /* Adjust the width of the label as needed */
        }
        .input-field {
            flex-grow: 1;
        }
        .stTextInput > div > div {
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )  
    qtext_table = rec['questiontext'].split('<br>')
    question_id_text = qtext_table[0]
    qtext_table = qtext_table[1:]
    qtext = "\n".join(qtext_table)
    qtext = text_field("Question Text", qtext)    
    option1 = text_field("Option A", rec['option1'])
    option2 = text_field("Option B", rec['option2'])
    option3 = text_field("Option C", rec['option3'])
    option4 = text_field("Option D", rec['option4'])
    answer = text_field("Answer", rec['answer'])
    soln = text_field("Solution", rec['soln'])
    if rec['language'] != 'EN':
        incorrect_feedback = text_field("Incorrect Feedback", rec['incorrect_feedback'])
    if rec['verifier_1'] is not None:
        verified1_date = rec['verifier1_date'].strftime('%d-%m-%Y @ %H:%M:%S')
        st.markdown(f"<p style='color:blue;'>1. Earlier Verified by User  {rec['verifier_1']} on -  {verified1_date}</p>", unsafe_allow_html=True)
    if rec['verifier_2'] is not None :
        verified2_date = rec['verifier2_date'].strftime('%d-%m-%Y @ %H:%M:%S')
        st.markdown(f"<p style='color:blue;'>2. Earlier Verified by User  {rec['verifier_2']} on -  {verified2_date}</p>", unsafe_allow_html=True)
    
    qtext = qtext.replace('\n', '<br>')
    qtext = question_id_text + '<br>' + qtext
    option1 = option1.replace('\n', '<br>')
    option2 = option2.replace('\n', '<br>')
    option3 = option3.replace('\n', '<br>')
    option4 = option4.replace('\n', '<br>')    
    soln = soln.replace('\n', '<br>')
    if rec['language'] != 'EN':
        incorrect_feedback = incorrect_feedback.replace('\n', '<br>')
    else:
        incorrect_feedback = rec['incorrect_feedback']

    struc = {
        'language': rec['language'],
        'moodle_id': rec['moodle_id'],
        'questiontext': qtext,
        'moodle_qno' : rec['moodle_qno'],
        'option1': option1,
        'option2': option2,
        'option3': option3,
        'option4': option4,
        'answer': answer,
        'soln': soln,
        'incorrect_feedback': incorrect_feedback
    }
        
    return struc

def display_changes(change_ind, label, orig_text, mod_text):
        
    if change_ind == "":
        st.divider()
        st.write(f":blue[Below Changes were done]")
    
    display_text, latex_ind = format_latex(orig_text)
    if latex_ind == "X":
        st.latex(display_text)
    else:
        st.write(f":red[Original {label} : ]" + orig_text)

    display_text, latex_ind = ""
    display_text, latex_ind = format_latex(mod_text)
    if latex_ind == "X":
        st.latex(display_text)
    else:
        st.write(f':green[Updated {label} : ]' + mod_text)

    change_ind = "X"

    return change_ind 
def show_modified_data(orig_record, mod_record):
    #w_count = 0
    w_changed = ""
    # Replace space begin and end of the string
    orig_record['questiontext'] = orig_record['questiontext'].strip()
    orig_record['option1'] = orig_record['option1'].strip()
    orig_record['option2'] = orig_record['option2'].strip()
    orig_record['option3'] = orig_record['option3'].strip()
    orig_record['option4'] = orig_record['option4'].strip()
    orig_record['answer'] = orig_record['answer'].strip()
    orig_record['soln'] = orig_record['soln'].strip()
    if orig_record['language'] != 'EN':
        orig_record['incorrect_feedback'] = orig_record['incorrect_feedback'].strip()
    if orig_record['soln'][-1] != '.':
        orig_record['soln'] = orig_record['soln'] + '.'
    mod_record['questiontext'] = mod_record['questiontext'].strip()
    mod_record['option1'] = mod_record['option1'].strip()
    mod_record['option2'] = mod_record['option2'].strip()
    mod_record['option3'] = mod_record['option3'].strip()
    mod_record['option4'] = mod_record['option4'].strip()
    mod_record['answer'] = mod_record['answer'].strip()
    mod_record['soln'] = mod_record['soln'].strip()
    if mod_record['language'] != 'EN':
        mod_record['incorrect_feedback'] = mod_record['incorrect_feedback'].strip()
    if mod_record['soln'][-1] != '.':
        mod_record['soln'] = mod_record['soln'] + '.'

    if orig_record['questiontext'] != mod_record['questiontext']:
        w_changed = display_changes(w_changed, "Question Test", orig_record['questiontext'], mod_record['questiontext'])
        
    if orig_record['option1'] != mod_record['option1']:
        w_changed = display_changes(w_changed, "Option 1", orig_record['option1'], mod_record['option1'])
        
    if orig_record['option2'] != mod_record['option2']:
        w_changed = display_changes(w_changed, "Option 2", orig_record['option2'], mod_record['option2'])
                
    if orig_record['option3'] != mod_record['option3']:
        w_changed = display_changes(w_changed, "Option 3", orig_record['option3'], mod_record['option3'])
        
    if orig_record['option4'] != mod_record['option4']:
        w_changed = display_changes(w_changed, "Option 4", orig_record['option4'], mod_record['option4'])
        
    if orig_record['answer'] != mod_record['answer']:
        w_changed = display_changes(w_changed, "Answer", orig_record['answer'], mod_record['answer'])
        
    if orig_record['soln'] != mod_record['soln']:
        w_changed = display_changes(w_changed, "Solution", orig_record['soln'], mod_record['soln'])
        
    if orig_record['language'] != 'EN':
        if orig_record['incorrect_feedback'] != mod_record['incorrect_feedback']:
            w_changed = display_changes(w_changed, "Incorrect Feedback", orig_record['incorrect_feedback'], mod_record['incorrect_feedback'])
            

def update_table(current_record, updated_data):
    w_connection = aws_start_connection()
    conn = w_connection[0]
    cursor = w_connection[1]
    moodle_id = current_record['moodle_id']
    questiontext = updated_data['questiontext']
    option1 = updated_data['option1']
    option2 = updated_data['option2']
    option3 = updated_data['option3']
    option4 = updated_data['option4']
    answer = updated_data['answer']
    soln = updated_data['soln']
    if current_record['language'] != 'EN':
        incorrect_feedback = updated_data['incorrect_feedback']
    else:
        incorrect_feedback = current_record['incorrect_feedback']
    if current_record['verifier_1'] == None:
        verifier_1 = st.session_state.user_id
        verifier1_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        verifier_2 = current_record['verifier_2']
        verifier2_date = current_record['verifier2_date']
    else:
        verifier_1 = current_record['verifier_1']
        verifier1_date = current_record['verifier1_date']
        if current_record['verifier_2'] != st.session_state.user_id and current_record['verifier_1'] != st.session_state.user_id:
            verifier_2 = st.session_state.user_id
            verifier2_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            verifier_2 = current_record['verifier_2']
            verifier2_date = current_record['verifier2_date']

    try:
        cursor.execute("UPDATE AWS_MOODLE_QUESTIONS SET questiontext = ?, option1 = ?, option2 = ?, option3 = ?, option4 = ?, answer = ?, soln = ?, incorrect_feedback = ?, verifier_1 = ?, verifier1_date = ?, verifier_2 = ?, verifier2_date = ? WHERE moodle_id = ?", (questiontext, option1, option2, option3, option4, answer, soln, incorrect_feedback, verifier_1, verifier1_date, verifier_2, verifier2_date, moodle_id))
        conn.commit()
        #st.success("Record has been updated successfully")
    except pyodbc.Error as e:
        error_found = "true"       
        st.error(f"An error occurred connecting to AWS database : {e}")
        sys.exit()
    
    return


def check_user_credentials(user_id, pw):
    valid_user = ""
    w_connection = aws_start_connection()
    conn = w_connection[0]
    cursor = w_connection[1]
    #user_id = 'AKSHAYE'
    password = pw.encode()
    try:
        # cursor.execute("INSERT INTO AWS_USERS VALUES(?,?)", (user_id, password))
        # conn.commit()
        cursor.execute("SELECT * FROM AWS_USERS WHERE user_id = ? and password = ?", (user_id, password))
        columns = [column[0] for column in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, row)))

    except pyodbc.Error as e:
        error_found = "true"       
        st.write(f"An error occurred connecting to AWS_USERS database : {e}")
        sys.exit()

    conn.close()

    if len(rows) == 1:
        valid_user = 'X'  

    return valid_user

# Main

st.set_page_config(page_title="Update Quiz Data", layout="wide")
  
w_select_subject = "Please Click here to Select Subject from the list below"
w_select_quiz_no = "Please Click here to Select Quiz No from the list below"
subject_options = get_subject_options(w_select_subject)
language_options = get_language_options()
if 'main_subject' not in st.session_state:
    st.session_state.subject = w_select_subject
if 'main_language' not in st.session_state:
    st.session_state.language = 'EN - English'
if 'main_quiz_no' not in st.session_state:
    st.session_state.quiz_no = w_select_quiz_no
st.markdown("""
        <style>
               .block-container {
                    padding-top: 1.9rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """, unsafe_allow_html=True)
st.sidebar.title("Validate Quiz Data")
w_login_title = "Please enter your User ID"
if 'user_id' not in st.session_state:
    st.header("Please Login to Update Quiz Data")   
    user_id = st.text_input("User Id")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        valid_user = check_user_credentials(user_id, password)
        #if user_id == 'test' and password == 'test':
        if valid_user == 'X':
            st.session_state.user_id = user_id
            st.experimental_rerun()
        else:
            st.error("Invalid User Id or Password")
if 'user_id' in st.session_state:
        #st.header("Program to Update Quiz Data")  
        st.sidebar.write(f"### Welcome {st.session_state.user_id}")
        #st.session_state.user_name = user_name
        subject = st.sidebar.selectbox("Please Select the subject", subject_options, key="main_subject")
        if subject == w_select_subject:
            st.header("Program to Update Quiz Data")
        if subject != w_select_subject:
            language = st.sidebar.selectbox("Please Select the Language", language_options, key="main_language")
            quiz_no_table = get_quiz_no_table(subject, language, w_select_quiz_no)            
            if quiz_no_table != []:
                quiz_no = st.sidebar.selectbox("Please Select the Quiz No", quiz_no_table, key="main_quiz_no")
                
                if quiz_no == w_select_quiz_no:
                    st.header("Program to Update Quiz Data")
                if quiz_no != w_select_quiz_no :
                    qno_table = get_quiz_no_data(subject, language, quiz_no)
                    # if 'main_questn_no' not in st.session_state:
                    #     st.session_state.questn_no = 0
                    if 'default_index' not in st.session_state:
                        st.session_state.default_index = 0
                    
                    questn_no = st.sidebar.selectbox("Please Select the Question No", qno_table, index=st.session_state.default_index, key="main_questn_no")
                    down_load_button = st.sidebar.button("Download the Updated XML File")
                    if questn_no != "":
                        question_id = questn_no.split('-')[1]
                        current_qno = questn_no.split('-')[0]
                        current_qno = int(current_qno) - 1
                        if current_qno != st.session_state.default_index:
                            st.session_state.default_index = current_qno
                            st.experimental_rerun()                
                        #st.session_state.default_index = int(current_qno) - 1
                        
                        w_title = "NEET - " + subject.split('-')[1] + " - " + language.split('-')[1] 
                        w_title = w_title + " - Quiz " + str(quiz_no) + " - Question ID : " + question_id
                        st.subheader(f":blue[{w_title}]")                        
                        current_record = get_current_record(subject, language, quiz_no, question_id)
                        updated_data = edit_current_record(current_record)
                        show_modified_data(current_record, updated_data)

                        col1, col2, col3 = st.columns(3)
                        prev_button = next_button = ""
                        if st.session_state.default_index != 0:
                            prev_button = col1.button("Previous Question")
                        confirm_button = col2.button("Confirm Changes to this Record")
                        if st.session_state.default_index != 49:
                            next_button = col3.button("Next Question")
                        if prev_button:                    
                            st.session_state.default_index = int(st.session_state.default_index) - 1
                            st.experimental_rerun()                     
                        if next_button:                    
                            st.session_state.default_index = int(st.session_state.default_index) + 1                   
                            st.experimental_rerun()
                        if confirm_button:                            
                            update_table(current_record, updated_data)
                            st.session_state.default_index = int(st.session_state.default_index) + 1                   
                            st.experimental_rerun()
                
                    if down_load_button:
                        create_xml_file(subject, language, quiz_no)
                #st.write(f"### Selected Subject: {subject}  Selected Language: {language} Selected Quiz No: {quiz_no}")
#st.title("Please upload XML file to display/edit the data")
# xml_table, new_filename = get_data_from_xml()       #Get the data from the XML file
# if len(xml_table) > 0 :
#     #display_data(xml_table)                             #Display the original data
#     updated_data = edit_data(xml_table)                 #Edit the data
#     final_updated_data, w_count = compare_original_and_updated_data(xml_table, updated_data)
#     if w_count != 0:
#         # st.write("### Updated Data:")
#         # st.dataframe(final_updated_data)
#         #xml_data = updated_data.to_dict('records')          #Converting the updated data dataframe to dictionary format
#         create_xml(final_updated_data,new_filename)               #Once submitted, the updated XML file is created and saved in the folder path mentioned
