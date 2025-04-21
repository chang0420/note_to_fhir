import re
import pandas as pd
from transformers import BartForConditionalGeneration, BartTokenizer
import glob
import json

bart_model_name = "facebook/bart-large-cnn"
bart_tokenizer = BartTokenizer.from_pretrained(bart_model_name)
bart_model = BartForConditionalGeneration.from_pretrained(bart_model_name)

def load_texts(file_paths):
    text = ""
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            text += content + "\n"
            print(f"讀取 {file_path} 的內容:\n{content}\n")
    return re.sub(r'\n\s*\n+', '\n', text.strip())

def generate_summary_with_bart(text, tokenizer, model):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=1024)
    summary_ids = model.generate(
        inputs["input_ids"],
        max_length=600,
        min_length=100,
        length_penalty=2.0,
        num_beams=4
    )
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True, clean_up_tokenization_spaces=False)

def create_hospital_course(subject_id, summaries):
    return {
        "resourceType": "Procedure",
        "id": f"ProcedureHospitalCourse-{subject_id}",
        "status": "completed",
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "8648-8"
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{subject_id}"
        },
        "encounter": {
            "reference": f"Encounter/{subject_id}"
        },
        "note": [
            {
                "text": f"{summaries}"
            }
        ]
    }

def hospital_course_frist(files_text, pt_id):
    summary = generate_summary_with_bart(files_text, bart_tokenizer, bart_model)
    hospital_course_resource = create_hospital_course(pt_id, summary)
    
    return hospital_course_resource