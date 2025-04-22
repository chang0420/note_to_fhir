# -*- coding: utf-8 -*-
"""
Created on Tue Apr 22 00:11:20 2025

@author: user
"""

from impression import create_impression_observation, create_icd_mapping
from dischargediagnoses import create_diagnoses_first
from chiefcomplaint import create_chief_complaint_observation
from presentIllness import create_presentIllness_observation
from physicalexamination import physical_exam_frist
from laboratorydata import create_ecg_observation
from surgicalmethod import create_procedure
from imagingstudy import create_text_observation
from hospitalcourse import hospital_course_frist, load_texts
from medicalrequest import format_discharge_medications, create_fhir_medication_request
from comorbidities_and_complications import map_comorbidities_to_icd9, create_comorbidities_and_complications
import pandas as pd
import re
import json
import glob




def clean_text(text):
    text = str(text)
    text = re.sub(r'_+|[-]{10,}|[=]{10,}', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'([.,():])(\1+)', r'\1', text)
    text = text.lower().strip()
    return text

def init_summary(subject_id, hadm_id, patient_meta):
    summary = {
        "resourceType": "Composition",
        "id": f"discharge-summary-{hadm_id}",
        "status": "final",
        "type": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "18842-5",
                "display": "Hospital discharge summary"
            }]
        },
        "subject": {"reference": f"Patient/{subject_id}"},
        "date": patient_meta["dischtime"],
        "author": [{"reference": "Practitioner/123"}],
        "title": "Discharge Summary",
        "section": []
    }
    return summary

def create_discharge_summary(noteevents, d_icd_diagnoses, radiology_df, icd_df, ecg_df,
                             procedures_df, text_files, medications_df, admissions_df):
    # 讀取患者基本資訊
    subject_id = int(admissions_df.loc[0, "subject_id"])
    hadm_id    = int(admissions_df.loc[0, "hadm_id"])
    dischtime  = admissions_df.loc[0, "dischtime"]
    patient_meta = {"dischtime": dischtime}

    # 初始化 summary
    summary = init_summary(subject_id, hadm_id, patient_meta)

    # 1. 出院診斷
    diag_json = create_diagnoses_first(noteevents, d_icd_diagnoses)
    summary["section"].append({
        "title": "Discharge Diagnoses",
        "content": diag_json
    })

    # 2. 影像檢查 Impression
    icd_map = create_icd_mapping(icd_df)
    first_rad = {k.upper(): v for k, v in radiology_df.iloc[0].to_dict().items()}
    imp_json = create_impression_observation(first_rad, icd_map)
    summary["section"].append({
        "title": "Radiology Impression",
        "content": [imp_json]
    })

    # 3. 主訴 Chief Complaint
    cc_json = create_chief_complaint_observation(first_rad, icd_map)
    summary["section"].append({
        "title": "Chief Complaint",
        "content": [cc_json]
    })

    # 4. 現病史 Present Illness
    pi_json = create_presentIllness_observation(first_rad, icd_map)
    summary["section"].append({
        "title": "History of Present Illness",
        "content": [pi_json]
    })

    # 5. 影像檢查報告 Imaging Study
    img_json = create_text_observation(first_rad, icd_map)
    summary["section"].append({
        "title": "Imaging Study",
        "content": [img_json]
    })

    # 6. 理學檢查 Physical Exam
    exam_notes = noteevents[noteevents["category"] == "Echo"]
    phys_json = physical_exam_frist(exam_notes.sort_values(["charttime","chartdate"]))
    summary["section"].append({
        "title": "Physical Examination",
        "content": phys_json
    })

    # 7. 手術處置 Procedures
    proc_json = [create_procedure(r) for r in procedures_df.to_dict("records")]
    summary["section"].append({
        "title": "Procedures",
        "content": proc_json
    })

    # 8. ECG
    ecg_row = {k.upper(): v for k, v in ecg_df.iloc[0].to_dict().items()}
    ecg_json = create_ecg_observation(ecg_row)
    summary["section"].append({
        "title": "ECG",
        "content": [ecg_json]
    })

    # 9. Hospital Course
    texts = load_texts(text_files)
    print(f"住院說明:{texts}")
    hc_json = hospital_course_frist(texts, subject_id)
    summary["section"].append({
        "title": "Hospital Course",
        "content": hc_json
    })
    print(f"住院經歷:{hc_json}")

    # 10. 出院用藥 Discharge Medications
    med_text = format_discharge_medications(medications_df, admissions_df["dischtime"])
    med_req  = create_fhir_medication_request(medications_df, admissions_df["dischtime"])
    summary["section"].append({
        "title": "Medications Instructions",
        "content": med_text
    })
    summary["section"].append({
        "title": "Medication Requests",
        "content": med_req
    })

    return summary
