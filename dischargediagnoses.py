# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 23:59:31 2025

@author: user
"""

from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import re
from datetime import datetime

model_name = "emilyalsentzer/Bio_ClinicalBERT"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)



def create_diagnoses_first(patient_notes, d_icd_diagnoses):
    subject_id = patient_notes["subject_id"]
    hadm_id = patient_notes["hadm_id"]
    diagnosis_keywords = d_icd_diagnoses['long_title'].tolist()
    
    diagnoses_embeddings = {c: get_embedding(c) for c in diagnosis_keywords}
    
    all_detected_diagnoses = set() 

    for _, row in patient_notes.iterrows():
       
        patient_text = row['cleaned_text']
        patient_embedding = get_embedding(patient_text)

    
        for condition, embedding in diagnoses_embeddings.items():
            similarity = cosine_similarity([patient_embedding], [embedding])[0][0]
            if similarity > 0.8:  
                all_detected_diagnoses.add(condition)  


    
    all_detected_diagnoses_array = list(all_detected_diagnoses)


    icd_mapping = dict(zip(d_icd_diagnoses['long_title'], d_icd_diagnoses['icd9_code']))

    
    detected_diagnoses_with_codes = [
        {"Diagnosis": diagnosis, "ICD_Code": icd_mapping.get(diagnosis, "Unknown")}
        for diagnosis in all_detected_diagnoses_array
    ]


    
    discharge_diagnoses_resources = [
        create_dischargediagnoses(entry["Diagnosis"], entry["ICD_Code"])
        for entry in detected_diagnoses_with_codes
    ]
    
    return discharge_diagnoses_resources


def normalize_comorbidity(comorb):
    return comorb.replace('\\r', '').strip()


def map_diagnoses_to_icd9(diagnoses, mapping_df):
    mapping_results = {}
    for comorb in diagnoses:
        norm_comorb = normalize_comorbidity(comorb)
        #print(norm_comorb)
        matches = mapping_df[mapping_df['diagnoses'].str.lower().str.contains(norm_comorb.lower(), na=False)]
        if not matches.empty:
            mapping_results[norm_comorb] = matches.iloc[0]['icd9_code']
        else:
            mapping_results[norm_comorb] = None
    return mapping_results



def create_dischargediagnoses(diagnosis, icd_code):
    """FHIR Discharge Diagnosis"""
    now = datetime.now()
    iso_charttime = now.isoformat()


    discharge_diagnosis_resource = {
        "resourceType": "Condition",
        "id": f"DischargeDiagnosis-{subject_id}",
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "resolved",
                    "display": "Resolved"
                }
            ],
            "text": "Resolved"
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "34117-2",
                        "display": "Discharge diagnosis"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": icd_code,
                    "display": diagnosis
                }
            ],
            "text": diagnosis
        },
        "subject": {
            "reference": f"Patient/{subject_id}"
        },
        "encounter": {
            "reference": f"Encounter/{subject_id}"
        },
        "recordedDate": iso_charttime,
    }

    return discharge_diagnosis_resource


def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :].squeeze().numpy()

