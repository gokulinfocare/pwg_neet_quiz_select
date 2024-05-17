# Streamlit XML Edit App using Select Box
import streamlit as st 
import xml.etree.ElementTree as ET
import sys
import pandas as pd
import base64
import os
from function_moodle_xml_create import create_moodle_xml
global_modified_qno = []
# Function to get data from XML file
def get_data_from_xml(w_select_text):
    global global_modified_qno
    xml_table = []              # List to store the data from XML file
    new_filename = "updated.xml"   # Default name for updated XML file
    moodle_qno_table = []
    st.set_page_config(page_title="Please upload XML file to display/edit the data", layout="wide")
    
    file_name = st.file_uploader("Choose the XML file you want to display/edit")
    if file_name is not None:
        new_filename = file_name.name[:-4] + "updated.xml"
        file_contents = file_name.read().decode("utf-8")
        root = ET.fromstring(file_contents)
        xml_table = []
        moodle_qno_table = []
        count = 0
        #Takes data from the XML file uploaded and stores it in a list of dictionaries
        for element in root.findall('.//question'):
            if element.attrib['type'] == 'multichoice':
                moodle_id = qtext = soln = option1 = option2 = option3 = option4 = answer = ''     
                moodle_id = element.find('.//name/text').text
                qtext = element.find('.//questiontext/text').text
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
                # Get Moodle Question Number
                start = qtext.find('Question ID:') + len('Question ID:')
                end = qtext.find('<br>', start)
                moodle_qno = qtext[start:end].strip()
                moodle_qno = moodle_qno.rstrip()
                moodle_qno = moodle_qno.lstrip()
                struc = {
                    'moodle_qno': moodle_qno,
                    'moodle_id': moodle_id,
                    'questiontext': qtext,                    
                    'option1': option1,
                    'option2': option2,
                    'option3': option3,
                    'option4': option4,
                    'answer': answer,
                    'soln': soln,
                    'incorrect_feedback': w_incorrect_feedback
                }
                xml_table.append(struc)                
                count += 1
                moodle_qno = str(count) + " - " + moodle_qno
                if moodle_qno_table == []:
                    moodle_qno_table.append(w_select_text)
                moodle_qno_table.append(moodle_qno)
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

        for rec in global_modified_qno:
            for i in range(len(moodle_qno_table)):                
                    if rec == moodle_qno_table[i]:
                        moodle_qno_table[i] = moodle_qno_table[i] + " - Validated"
                        break
                        
    return xml_table , moodle_qno_table, new_filename         # Return the data and new filename

def edit_data(data):
    st.write("### Edit Data:")
    num_rows = len(data)

    # Get column names from the keys of the first dictionary in the list
    if num_rows > 0:
        column_names = list(data[0].keys())
    else:
        column_names = []

    column_names = column_names[2:]   # No need to show the Qno and Moodle ID
    # Create empty DataFrame with columns
    edited_data = pd.DataFrame(columns=column_names, index=range(num_rows))
    data = pd.DataFrame(data)           #Convert the list of original data to a dataframe
    for i in range(len(data)):
        count = 0        
        for col in data.columns:
            count += 1
            if count < 3:
                continue
            if len(data.at[i, col]) > 180:     #If the length of the data is more than 180 chars
                edited_data.at[i, col] = st.text_area(f"Row {i+1} - {col}", data.at[i, col],  height=125)
            else:
                edited_data.at[i, col] = st.text_input(f"Row {i+1} - {col}", data.at[i, col])   #Edits the data in the dataframe
    return edited_data

# Main

w_select_text = "Please Click here to Select from the list below"

if 'main_option' not in st.session_state:
    st.session_state.option = w_select_text

xml_table, moodle_qno_table, new_filename = get_data_from_xml(w_select_text)       #Get the data from the XML file
if 'moodle_qno_table' not in st.session_state:
    st.session_state.moodle_qno_table = moodle_qno_table
else:
    for rec in global_modified_qno:
            for i in range(len(moodle_qno_table)):                
                    if rec == moodle_qno_table[i]:
                        moodle_qno_table[i] = moodle_qno_table[i] + " - Validated"
                        st.write("Hello" + user_selected_qno)
                        st.session_state.moodle_qno_table = moodle_qno_table
                        break

if len(xml_table) > 0 :
    for rec in global_modified_qno:
            for i in range(len(moodle_qno_table)):                
                    if rec == moodle_qno_table[i]:
                        moodle_qno_table[i] = moodle_qno_table[i] + " - Validated"
                        st.write("Hello" + user_selected_qno)
                        break
    st.session_state.moodle_qno_table = moodle_qno_table
    st.session_state.option = st.selectbox( 'Please Select Moodle Question Number', moodle_qno_table, key="main_option" ) 
    if st.session_state.option != w_select_text:
        user_selected_qno = st.session_state.option        
        selected_qno = st.session_state.option.split(" - ")[1]
        selected_qno = selected_qno.replace(" - Validated", "")
        selected_qno = selected_qno.rstrip()
        selected_qno = selected_qno.lstrip()
        selected_rec = []
        for rec in xml_table:
            if rec['moodle_qno'] == selected_qno:
                selected_rec.append(rec)
                break
        with st.form('my_form'):
            st.subheader('**Validate the Question**')

            # Input widgets
            if len(selected_rec[0]['questiontext']) > 180:
                qtext = st.text_area('Question Text', selected_rec[0]['questiontext'], height=125)
            else:
                qtext = st.text_input('Question Text', selected_rec[0]['questiontext'])
            if len(selected_rec[0]['option1']) > 180:
                option1 = st.text_area('Option 1', selected_rec[0]['option1'], height=125)
            else:
                option1 = st.text_input('Option 1', selected_rec[0]['option1'])
            if len(selected_rec[0]['option2']) > 180:
                option2 = st.text_area('Option 2', selected_rec[0]['option2'], height=125)
            else:
                option2 = st.text_input('Option 2', selected_rec[0]['option2'])
            if len(selected_rec[0]['option3']) > 180:
                option3 = st.text_area('Option 3', selected_rec[0]['option3'], height=125)
            else:
                option3 = st.text_input('Option 3', selected_rec[0]['option3'])
            if len(selected_rec[0]['option4']) > 180:
                option4 = st.text_area('Option 4', selected_rec[0]['option4'], height=125)
            else:
                option4 = st.text_input('Option 4', selected_rec[0]['option4'])
            answer = st.text_input('Answer', selected_rec[0]['answer'])
            if len(selected_rec[0]['soln']) > 180:
                soln = st.text_area('Solution Long', selected_rec[0]['soln'], height=125)
            else:
                soln = st.text_input('Solution Long', selected_rec[0]['soln'])           
            incorrect_feedback = st.text_input('Incorrect Feedback', selected_rec[0]['incorrect_feedback'])
            # Every form must have a submit button.
            submitted = st.form_submit_button('Question is Validated. Click to Save Changes')
            w_new_option = st.session_state.option
            if submitted:
                for i in range(len(moodle_qno_table)):                
                    if user_selected_qno == moodle_qno_table[i]:
                        if "Validated" not in moodle_qno_table[i]:
                            moodle_qno_table[i] = moodle_qno_table[i] + " - Validated"
                            w_new_option = moodle_qno_table[i]
                del st.session_state['main_option']
                st.session_state.main_option = w_new_option
                st.rerun()
                #del st.session_state['moodle_qno_table']
                #global_modified_qno.append(user_selected_qno)
                #global_modified_qno = list(dict.fromkeys(global_modified_qno))
                #st.write(global_modified_qno[0])
                #st.experimental_rerun()
                #for i in range(len(moodle_qno_table)):                
                #    if user_selected_qno == moodle_qno_table[i]:
                #        moodle_qno_table[i] = moodle_qno_table[i] + " - Validated"
                        #del st.session_state['main_option']
                        #st.session_state.main_option = moodle_qno_table[i]
                #st.rerun()
        
        
        cancel = st.button('Cancel Changes')    
        
        if cancel:
            
            del st.session_state['main_option']
            st.session_state.main_option = w_select_text
            st.rerun()
        
         
           #updated_rec = edit_data(selected_rec)
