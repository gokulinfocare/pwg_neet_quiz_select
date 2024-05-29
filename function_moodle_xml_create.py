# This program creates Moodle XML File
import xml.etree.ElementTree as ET
import pyodbc
import sys
import re
import streamlit as st

def start_connection():
    conn = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};"
                "Server=LAPTOP-EITSFNFO;"
                "Database=RamaKrishna;"
                "Trusted_Connection=yes;")
    cursor = conn.cursor()
    return conn, cursor

def convert_math_delimiters(latex_string):
    new_string = ""
    i = 0
    try:
        while i < len(latex_string):
            if latex_string[i:i+2] == "$$":  # Check for display math start
                new_string += "\\["  # Replace with LaTeX display math start
                i += 2
                while i < len(latex_string) and latex_string[i:i+2] != "$$":
                    new_string += latex_string[i]
                    i += 1
                new_string += "\\]"  # Replace with LaTeX display math end
                i += 2  # Skip past the ending $$
            elif latex_string[i] == "$":  # Check for inline math start
                new_string += "\\("  # Replace with LaTeX inline math start
                i += 1
                while i < len(latex_string) and latex_string[i] != "$":
                    new_string += latex_string[i]
                    i += 1
                new_string += "\\)"  # Replace with LaTeX inline math end
                i += 1  # Skip past the ending $
            else:
                new_string += latex_string[i]
                i += 1
            
    except IndexError:
        pass
    return new_string

def convert_new_line(stringstr):
    new_string = stringstr
    return new_string
    new_string = ""
    i = 0
    try:
        while i < len(stringstr):
            if stringstr[i:i+2] == "/n" or stringstr[i:i+2] == r"\n":  # Check for display math start
                new_string += "<br>"  # Replace with LaTeX display math start
                i += 2
            else:
                new_string += stringstr[i]
                i += 1
    except IndexError:
        pass
    return new_string


def update_moodle_question_numbers_table(cursor, moodle_id):

    breakpoint()
    # No need to open connection becasuse this is called within a connection
    moodle_id_like = moodle_id[:3] + "%"
    try:
        cursor.execute("SELECT MAX(moodle_qno) FROM MOODLE_QUESTION_NUMBERS WHERE moodle_id LIKE ? ", (moodle_id_like, ))
        rows = cursor.fetchall()
        max_value = rows[0][0]
        max_value = max_value + 1
        cursor.execute("INSERT INTO MOODLE_QUESTION_NUMBERS (moodle_id, moodle_qno) VALUES (?, ?)", (moodle_id, max_value))
    except pyodbc.Error as e:
            error_found = "true"       
            print(f"An error occurred getting Highest Number from MOODLE_QUESTION_NUMBERS : {e}")

    return max_value



    return moodle_qno


def get_moodle_qn(moodle_id):

    w_connection = start_connection()
    conn = w_connection[0]
    cursor = w_connection[1]
    rows = []
    moodle_qno = ""
    try:
        cursor.execute("SELECT * FROM MOODLE_QUESTION_NUMBERS WHERE moodle_id = ?", (moodle_id))
        # get column names from cursor.description
        columns = [column[0] for column in cursor.description]

        # fetch all rows, and create a list of dictionaries         # each dictionary represents a row      
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, row)))
        moodle_qno_prefix = moodle_id[2:3]
        if len(rows) == 0:       # Moodle qno not found, so create one
            moodle_qno = update_moodle_question_numbers_table(cursor, moodle_id)
            moodle_qno = moodle_qno_prefix + str(moodle_qno)
        else:
            moodle_qno = moodle_qno_prefix + str(rows[0]['moodle_qno'])           


    except pyodbc.Error as e:
            error_found = "true"       
            print(f"An error occurred reading table MOODLE_QUESTION_NUMBERS : {e}")
            conn.close()
            sys.exit()

    conn.close()


    return moodle_qno


def prepare_correctfeedback_text_lang(w_correct_answer,w_correctfeedback, w_lang):

    try:
        w_en_correct_answer = w_correct_answer.split("<br>")[0]

        if 'Your answer is incorrect' in w_correctfeedback:      # We need to remove and replace with latest
            input_table = w_correctfeedback.split("<br>")
            if "Your answer is incorrect" in input_table[0]:
                input_table = input_table[1:]
            if "Correct answer is:" in input_table[0]:
                input_table = input_table[1:]
            if input_table[0] == "":
                input_table = input_table[1:]
        w_new_text = "Your answer is incorrect" + "<br>Correct answer is: <strong>" + w_en_correct_answer + "</strong><br>" + w_lang  + "<br>" + w_correctfeedback

    except Exception as e:
        print(f"Error in prepare_correctfeedback_text_lang : {e}")
        sys.exit()

    return w_new_text

def prepare_correctfeedback_text_en(w_correct_answer,w_correctfeedback):

    if "Your answer is incorrect" in w_correctfeedback:
        input_table = w_correctfeedback.split("<br>")
        if "Your answer is incorrect" in input_table[0]:
            input_table = input_table[1:]
        if "Correct answer is:" in input_table[0]:
            input_table = input_table[1:]
        if input_table[0] == "":
            input_table = input_table[1:]
        w_correctfeedback = "<br>".join(input_table)

    w_new_text = "Your answer is incorrect" + "<br>Correct answer is: <strong>" + w_correct_answer + "</strong><br>" 
    w_new_text = w_new_text  + w_correctfeedback

    return w_new_text

def format_option_incorrect_answer(w_correct_answer):

    w_new_text = "Your answer is incorrect" + "<br>Correct answer is: <strong>" + w_correct_answer + "</strong>"

    return w_new_text

def check_replace_duplicate(option):
    option_new = option
    # w_split = option.split("<br>")
    # # Check if EN and other language options are same
    # if len(w_split) == 2:
    #     if w_split[0] == w_split[1]:
    #         option_new = w_split[0]
    #         return option_new
    # if len(w_split) > 1:    
    #     w_en_option = w_split[0]
    #     w_lang_option = w_split[1]
    #     w_en_option_table = w_en_option.split(" ")
    #     w_lang_option_table = w_lang_option.split(" ")
    #     # If the option split contains 2 parts and one part is same in both then use only english
    #     if len(w_en_option_table) == 2 and len(w_lang_option_table) == 2:
    #         if (w_en_option_table[0] == w_lang_option_table[0]) or (w_en_option_table[1] == w_lang_option_table[1]):
    #             option_new = w_en_option
    #             return option_new
            
    #     # If the option split contains 3 parts and if two parts are same then use only english
    #     if len(w_en_option_table) == 3 and len(w_lang_option_table) == 3:
    #         w_count = 0
    #         if w_en_option_table[0] == w_lang_option_table[0]:
    #             w_count += 1
    #         if w_en_option_table[1] == w_lang_option_table[1]:
    #             w_count += 1
    #         if w_en_option_table[2] == w_lang_option_table[2]:
    #             w_count += 1
    #         if w_count >= 2:
    #             option_new = w_en_option
    #             return option_new
        
    return option_new 

def check_adjust_options(w_option1, w_option2, w_option3, w_option4):

    try:
        # Check if any one options does not have breaks, then we use only english        
        answer1 = w_option1
        answer2 = w_option2
        answer3 = w_option3
        answer4 = w_option4
        count_br1 = w_option1.count("<br>")
        count_br2 = w_option2.count("<br>")
        count_br3 = w_option3.count("<br>")
        count_br4 = w_option4.count("<br>")
        if count_br1 == count_br2 == count_br3 == count_br4 == 0:   # All options are in english
            return w_option1, w_option2, w_option3, w_option4
        
        # If any one option got zero then we use english only
        if count_br1 == 0 or count_br2 == 0 or count_br3 == 0 or count_br4 == 0:
            answer1 = w_option1.split("<br>")[0]
            answer2 = w_option2.split("<br>")[0]
            answer3 = w_option3.split("<br>")[0]
            answer4 = w_option4.split("<br>")[0]
            return answer1, answer2, answer3, answer4
    except Exception as e:
        print(f"Error in check_adjust_options : {e}")
        sys.exit()
    # We will add more logic here to adjust the options


    return answer1, answer2, answer3, answer4

def update_lang_incorrect_msg(input_text, w_correct_answer_mod_lang):

    try:
        output = input_text
        match = re.search('<strong>(.*?)</strong>', input_text)
        if match:
            data = match.group(1)
            output = input_text.replace(data, w_correct_answer_mod_lang)
    except Exception as e:
        print(f"Error in update_lang_incorrect_msg : {e}")
        sys.exit()          

    
    return output


def capitalize_first_letter(input_text):

    try:
        output_text = input_text
        output_text = output_text.strip()
        if output_text[0].islower():
            output_text = output_text[0].upper() + output_text[1:]

        # Split the input at . and capitalize the first letter of each sentence
        output_text = output_text.split(". ")
        new_text = []
        for rec in output_text:
            if rec == ' ':
                new_text.append(rec)
                continue
            rec = rec.strip()
            if ('\(' in rec) or ( '\)' in rec ) or ( 'math' in rec ) or ( '\[' in rec ) or ( ']\\' in rec) :
                new_text.append(rec)
                continue
            elif rec.isascii() and rec[0].islower():
                rec = rec[0].upper() + rec[1:]
                new_text.append(rec)
            else:
                new_text.append(rec)
            
        output_text = ". ".join(new_text)
    
    except Exception as e:
        print(f"Error in capitalize_first_letter : {e}, Text : {input_text}")
        sys.exit()

    
    return output_text

def remove_spaces(input_text):
    try:
        output_text = input_text 
        if "<p>" in output_text:
            output_text = output_text.replace("<p>", "").replace("</p>", "")

    except Exception as e:
        print(f"Error in remove_spaces : {e}")
        sys.exit()

    return output_text 

def remove_unnecessary_text(input_text, w_lang_xml):
    
    try:
        output_text = input_text
        if w_lang_xml == "":
            upper_text = input_text.upper()
            if "ON HOW THE ANSWER" in upper_text:
                start_position = upper_text.find("ON HOW THE ANSWER")
                end_position = start_position + 28
                if upper_text[end_position] == ":":
                    end_position += 1
                output_text = output_text[:start_position] + output_text[end_position:]
            upper_text = output_text.upper()
            
            if "ANSWER IS CORRECT:" in upper_text:
                # Check if line break is present
                if '<br>' in upper_text:
                    upper_text = upper_text.split('<br>')
                    if "ANSWER IS CORRECT:" in upper_text[0]:
                        if upper_text[1] == "2. : ":
                            skip_text = len(upper_text[0]) + len(upper_text[1]) + 1
                        else:
                            skip_text = len(upper_text[0]) + 1
                        
                        output_text = output_text[skip_text + 1:]
                else:
                    start_position = upper_text.find("ANSWER IS CORRECT:")
                    end_position = start_position + 18            
                    if upper_text[end_position:end_position + 11] == " YES 2. :  ":
                        end_position += 11            
                        
                    if upper_text[end_position:end_position + 4] == " YES":
                        end_position += 4
                        
                    output_text = output_text[:start_position] + output_text[end_position:]

            upper_text = output_text.upper()
                    
            if "---ANSWER: YES" in upper_text:
                start_position = upper_text.find("---ANSWER: YES")
                end_position = start_position + 14
                output_text = output_text[:start_position] + output_text[end_position:]

            upper_text = output_text.upper()
            
            if "ANSWER IS INVALID: NO," in upper_text:
                start_position = upper_text.find("ANSWER IS INVALID: NO,")
                end_position = start_position + 22
                output_text = output_text[:start_position] + output_text[end_position:]

            upper_text = output_text.upper()
            
            if "EXPLANATION:" in upper_text:
                output_text = output_text[12:]
            
            output_text = output_text.replace("**", "")
            output_text = output_text.replace("2. Detailed", "")
            #output_text = output_text.replace("\n", "<br>")
            if output_text[0] == " ":
                output_text = output_text[1:]
            if output_text[0] == " ":  # Check again
                output_text = output_text[1:]
            if output_text[:4] == "<br>":
                output_text = output_text[4:]
                if output_text[:4] == "<br>":
                    output_text = output_text[4:]
                if output_text[:2] == "  ":
                    output_text = output_text[2:]
                if output_text[0] == " ":  # Check again
                    output_text = output_text[1:]
            if output_text[:4] == "2. :":
                output_text = output_text[4:]
            if output_text[0] == " ":
                output_text = output_text[1:]
            if output_text[:11] == "Therefore, ":
                output_text = output_text[11:]                
                output_text = capitalize_first_letter(output_text)
            if output_text[-8:] == "Detailed":
                output_text = output_text[:-8]
            output_text = output_text.strip()
            # Below statement removes any text if the text is not ending with . This is only for English
            if output_text.isascii() and output_text[-1] != ".":
                output_text = output_text.rsplit(".", 1)[0] + "."
            

    except Exception as e:
        print(f"Error in remove_unnecessary_text : {e}")
        sys.exit()
   

    
    return output_text

def correct_formatting(input_text, w_lang_xml):

    input_text = input_text.strip()
    try:
        output_text = input_text
        if w_lang_xml == "":
            output_text = capitalize_first_letter(output_text)
        #Power of symbol
        output_text = re.sub(r'(\^)(\d+)', r'\(^{\2}\)', output_text)
        output_text = output_text.replace("\n", "<br>") 

    except Exception as e:
        print(f"Error in correct_formatting : {e}")
        sys.exit()

    return output_text

# def adjust_question_text(w_questiontext, w_lang_xml):

#     output_text = w_questiontext
#     if w_lang_xml == "X":
#         qn_table = w_questiontext.split('<br>')
#         # Remove top blank lines
#         while qn_table and qn_table[0] == '':
#             qn_table.pop(0) 
#         w_question_id = qn_table[0]
#         # Find the index of Question ID
#         index = w_questiontext.find(w_question_id)
#         qtext = ""
#         if index != -1:
#             # Add the length of "Question ID" to the index
#             index += len(w_question_id)
#             # Grab the substring after "Question ID"
#             qtext = w_questiontext[index:].strip()
#             # Remove any leading <br> tags - Loop 4 times to remove all
#             for i in range(4):
#                 if qtext[:4] == '<br>':
#                     qtext = qtext[4:]
        
#         output_text = w_question_id + "<br>" + qtext       


#     return output_text

def create_moodle_xml(questions):

    # Create the root element
    quiz = ET.Element("quiz")

    #for key, value in questions.items():
    for question in questions:
        # Naming conversion from different format to Moodle format
        w_questiontext = w_option1 = w_option2 = w_option3 = w_option4 = w_answer = w_correctfeedback = w_incorrectfeedback = ""
        moodle_id = moodle_qno = w_correct_answer = w_correct_answer_mod_lang = ""
        w_option1_lang = w_option2_lang = w_option3_lang = w_option4_lang = w_lang_xml = ""
        w_correct_answer_lang = w_incorrect_answer_msg = ""
        if "moodle_id" in question:
            moodle_id = question["moodle_id"]
        if 'questiontext' in question:
            w_questiontext = question['questiontext']
            if w_questiontext[-7:] == 'ptions:':  # Remove the last 8 characters
                w_questiontext = w_questiontext[:-8]
            if "Question ID: " not in w_questiontext:
                if 'moodle_qno' in question:
                    moodle_qno = moodle_id[2:3] + str(question['moodle_qno'])                 
                else:             #"Insert Moodle Question #
                    moodle_qno = get_moodle_qn(moodle_id)
                w_questiontext = "Question ID: " + moodle_qno + '<br>' + w_questiontext            
        if 'option1' in question:
            w_option1 = question['option1']
        elif 'answer1' in question:
            w_option1 = question['answer1']       
        if 'option2' in question:
            w_option2 = question['option2']
        elif 'answer2' in question:
            w_option2 = question['answer2']
        if 'option3' in question:
            w_option3 = question['option3']
        elif 'answer3' in question:
            w_option3 = question['answer3']
        if 'option4' in question:
            w_option4 = question['option4']
        elif 'answer4' in question:
            w_option4 = question['answer4']
        if 'answer' in question:
            w_answer = question['answer']
        if 'correctfeedback' in question:
            w_correctfeedback = question['correctfeedback']            
        elif 'soln_long' in question:
            if question['soln_long'] == None:
                w_correctfeedback = question['soln']
            else:
                w_correctfeedback = question['soln_long']
                #w_correctfeedback = question['soln']  # Too many corrections
        elif 'soln' in question:
            w_correctfeedback = question['soln']
        if not w_questiontext.isascii():
            w_lang_xml = "X"
        # In language transalates remove duplicates if options contains only numbers        
        #if 'incorrect_feedback' in question:    # This field only available in language transalation
        if w_lang_xml == "X":    
            w_option1_lang = w_option1
            w_option2_lang = w_option2
            w_option3_lang = w_option3
            w_option4_lang = w_option4
            w_option1 = check_replace_duplicate(w_option1)
            w_option2 = check_replace_duplicate(w_option2)
            w_option3 = check_replace_duplicate(w_option3)
            w_option4 = check_replace_duplicate(w_option4)
            w_option1, w_option2, w_option3, w_option4 = check_adjust_options(w_option1, w_option2, w_option3, w_option4)
            
        

        # Fix many issues in formatting
        w_questiontext = remove_spaces(w_questiontext)
        w_option1 = remove_spaces(w_option1)
        w_option2 = remove_spaces(w_option2)
        w_option3 = remove_spaces(w_option3)
        w_option4 = remove_spaces(w_option4)
        w_correctfeedback = remove_spaces(w_correctfeedback)        
        w_questiontext = correct_formatting(w_questiontext, w_lang_xml)
        w_option1 = correct_formatting(w_option1, w_lang_xml)
        w_option2 = correct_formatting(w_option2, w_lang_xml)
        w_option3 = correct_formatting(w_option3, w_lang_xml)
        w_option4 = correct_formatting(w_option4, w_lang_xml)
        w_correctfeedback = correct_formatting(w_correctfeedback, w_lang_xml)        
        # Remove the below code after testing
        #st.subheader(w_correctfeedback)
    # Remove the above code after testing
        # Remove unnecessary Text   
        w_correctfeedback = remove_unnecessary_text(w_correctfeedback, w_lang_xml)        

        
        

        # Check and convert the text into Moodle Format
        w_questiontext = convert_math_delimiters(w_questiontext)
        w_questiontext = convert_new_line(w_questiontext)
        w_option1 = convert_math_delimiters(w_option1)
        w_option1 = convert_new_line(w_option1)
        w_option2 = convert_math_delimiters(w_option2)
        w_option2 = convert_new_line(w_option2)
        w_option3 = convert_math_delimiters(w_option3)
        w_option3 = convert_new_line(w_option3)
        w_option4 = convert_math_delimiters(w_option4)
        w_option4 = convert_new_line(w_option4)        
        w_correctfeedback = convert_math_delimiters(w_correctfeedback)
        w_correctfeedback = convert_new_line(w_correctfeedback)        
        if w_answer.upper() == 'A':            
            w_correct_answer = w_option1
            if w_option1 != w_option1_lang:
                w_correct_answer_mod_lang = w_option1
        elif w_answer.upper() == 'B':
            w_correct_answer = w_option2
            if w_option2 != w_option2_lang:
                w_correct_answer_mod_lang = w_option2
        elif w_answer.upper() == 'C':
            w_correct_answer = w_option3
            if w_option3 != w_option3_lang:
                w_correct_answer_mod_lang = w_option3
        elif w_answer.upper() == 'D':
            w_correct_answer = w_option4
            if w_option4 != w_option4_lang:
                w_correct_answer_mod_lang = w_option4

        w_correct_answer_lang = ""
        if 'incorrect_feedback' in question and w_lang_xml == "X":
            if w_correct_answer_mod_lang != "":
                w_incorrect_answer_msg = update_lang_incorrect_msg(question['incorrect_feedback'], w_correct_answer_mod_lang)
            else:
                w_incorrect_answer_msg = question['incorrect_feedback']
            w_correct_answer_lang = w_incorrect_answer_msg            
        else:
            w_incorrect_answer_msg = format_option_incorrect_answer(w_correct_answer)
                
        question_element = ET.SubElement(quiz, "question", type="multichoice")
        title = ET.SubElement(question_element, "name")
        title_text = ET.SubElement(title, "text")
        title_text.text = moodle_id
        questiontext = ET.SubElement(question_element, "questiontext", format="html")
        questiontext_text = ET.SubElement(questiontext, "text")
        questiontext_text.text = w_questiontext  #question['questiontext']
        #correct_answer_index = ord(w_answer) - ord("A")

        # Options part
        fraction = "0"
        if w_answer.upper() == 'A':
            fraction = "100"
        answer_element = ET.SubElement(question_element, "answer", fraction=fraction)
        answer_text = ET.SubElement(answer_element, "text")
        answer_text.text = w_option1
        if w_answer.upper() != 'A':
            feedback_element = ET.SubElement(answer_element, "feedback")
            feedback_text = ET.SubElement(feedback_element, "text")
            feedback_text.text = w_incorrect_answer_msg
        
        fraction = "0"
        if w_answer.upper() == 'B':
            fraction = "100"
        answer_element = ET.SubElement(question_element, "answer", fraction=fraction)
        answer_text = ET.SubElement(answer_element, "text")
        answer_text.text = w_option2
        if w_answer.upper() != 'B':
            feedback_element = ET.SubElement(answer_element, "feedback")
            feedback_text = ET.SubElement(feedback_element, "text")
            feedback_text.text = w_incorrect_answer_msg

        fraction = "0"
        if w_answer.upper() == 'C':
            fraction = "100"
        answer_element = ET.SubElement(question_element, "answer", fraction=fraction)
        answer_text = ET.SubElement(answer_element, "text")
        answer_text.text = w_option3
        if w_answer.upper() != 'C':
            feedback_element = ET.SubElement(answer_element, "feedback")
            feedback_text = ET.SubElement(feedback_element, "text")
            feedback_text.text = w_incorrect_answer_msg

        fraction = "0"
        if w_answer.upper() == 'D':
            fraction = "100"     
        answer_element = ET.SubElement(question_element, "answer", fraction=fraction)
        answer_text = ET.SubElement(answer_element, "text")
        answer_text.text = w_option4
        if w_answer.upper() != 'D':
            feedback_element = ET.SubElement(answer_element, "feedback")
            feedback_text = ET.SubElement(feedback_element, "text")
            feedback_text.text = w_incorrect_answer_msg
        
        if w_correctfeedback:
            correctfeedback = ET.SubElement(question_element, "correctfeedback")
            feedback_text = ET.SubElement(correctfeedback, "text")
            feedback_text.text = w_correctfeedback  #question["correctfeedback"]
            incorrectfeedback = ET.SubElement(question_element, "incorrectfeedback")
            incorrectfeedback_text = ET.SubElement(incorrectfeedback, "text")
            if 'incorrect_feedback' in question and w_lang_xml == "X":
                incorrectfeedback_mod_text = prepare_correctfeedback_text_lang(w_correct_answer,w_correctfeedback, w_correct_answer_lang )
            else:
                incorrectfeedback_mod_text = prepare_correctfeedback_text_en(w_correct_answer,w_correctfeedback )
            
            incorrectfeedback_text.text = incorrectfeedback_mod_text   #"Your answer is incorrect."
        show_instruction = ET.SubElement(question_element, "showstandardinstruction")
        show_instruction.text = "0"

    output_xml = ET.tostring(quiz, encoding="unicode")
    # with open(file_name, 'w', encoding='utf-8') as file:
    #         file.write(output_xml)
    return output_xml

