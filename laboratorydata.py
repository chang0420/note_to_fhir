# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 16:37:11 2025

@author: user
"""
from datetime import datetime

def create_ecg_observation(row):
    subject_id = row['SUBJECT_ID']
    category = row['CATEGORY']
    text = row['TEXT']
    text = text.replace("\n", " ")
    charttime = row['CHARTDATE']
    iso_charttime = datetime.strptime(charttime, "%Y-%m-%d %H:%M:%S").isoformat()

    condition_resource = {
        "resourceType": "Observation",
        "id": f"ObservationLaboratory-{subject_id}",
        "status":"final",
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "resmission",
                    "display": "Remission"
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "30954-2",

                    }
                ],
                "text": "特殊檢查"
            }
        ],
        "code": {
            "text": category
        },
        "subject": {
            "reference": f"Patient/{subject_id}"
        },
        "encounter": {
            "reference": f"Encounter/{subject_id}"
        },
        "effectiveDateTime": iso_charttime,
        "valueString": text
    }

    return condition_resource

def create_icd_mapping(icd_df):
    icd_mapping = {}
    for _, row in icd_df.iterrows():
        # 將 subject_id 轉換為字串
        subject_id = str(row['subject_id'])
        icd_entry = {
            'icd9_code': row['icd9_code'],
            'long_title': row['long_title']
        }

        if subject_id not in icd_mapping:
            icd_mapping[subject_id] = []

        icd_mapping[subject_id].append(icd_entry)

    return icd_mapping

