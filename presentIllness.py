# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 15:04:27 2025

@author: user
"""

import json
import ast


def create_chief_complaint_observation(row, icd_mapping):
    subject_id = row['SUBJECT_ID']
    row_id = row['ROW_ID']

    try:
        key_info = json.loads(row['KEY_INFO'])
    except json.JSONDecodeError:
        key_info = ast.literal_eval(row['KEY_INFO'])
        print(f"Decoding JSON in row {row_id}: {row['KEY_INFO']}")


    chief_complaint = key_info.get("medical history", "")


    if not chief_complaint:
        chief_complaint = key_info.get("reason", "")

    first_icd_code = ""
    first_icd_title = ""
    subject_id_str = str(subject_id)

    if subject_id_str in icd_mapping and icd_mapping[subject_id_str]:
        first_icd_code = icd_mapping[subject_id_str][0]['icd9_code']
        first_icd_title = icd_mapping[subject_id_str][0]['long_title']
    else:
        print(f"No ICD codes found for subject {subject_id}")

    condition_resource = {
        "resourceType": "Condition",
        "id": f"Condition-{subject_id}",
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
                        "code": "10164-2",
                        "display": "History of Presnet illness Narrative"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://twcore.mohw.gov.tw/ig/twcore/CodeSystem/icd-10-2021-cm-tw",
                    "code": first_icd_code,
                    "display": first_icd_title
                }
            ],
            "text": chief_complaint
        },
        "subject": {
            "reference": f"Patient/{subject_id}"
        },
        "encounter": {
            "reference": f"Encounter/{subject_id}"
        }
    }

    return condition_resource

def create_icd_mapping(icd_df):
    icd_mapping = {}
    for _, row in icd_df.iterrows():
        subject_id = str(row['subject_id'])
        icd_entry = {
            'icd9_code': row['icd9_code'],
            'long_title': row['long_title']
        }

        if subject_id not in icd_mapping:
            icd_mapping[subject_id] = []

        icd_mapping[subject_id].append(icd_entry)

    return icd_mapping

