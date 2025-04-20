# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 22:06:19 2025

@author: user
"""

import csv
import json
from datetime import datetime
import ast
import pandas as pd

def create_impression_observation(row, icd_mapping):
  
    subject_id = row['SUBJECT_ID']
    hadm_id = row['HADM_ID']
    row_id = row['ROW_ID']
    charttime = row['CHARTTIME']

    
    try:
        key_info = json.loads(row['KEY_INFO'])
    except json.JSONDecodeError:
        key_info = ast.literal_eval(row['KEY_INFO'])
        print(f"Decoding JSON in row {row_id}: {row['KEY_INFO']}")

   
    impression = key_info.get("impression", "")

    
    if not impression:
        impression = key_info.get("medical condition", "")

    
    iso_charttime = datetime.strptime(charttime, "%Y-%m-%d %H:%M:%S").isoformat()

    
    first_icd_code = ""
    first_icd_title = ""

    
    subject_id_str = str(subject_id)

    if subject_id_str in icd_mapping and icd_mapping[subject_id_str]:
        first_icd_code = icd_mapping[subject_id_str][0]['icd9_code']
        first_icd_title = icd_mapping[subject_id_str][0]['long_title']
    else:
        print(f"No ICD codes found for subject {subject_id}")

    
    observation_resource = {
        "resourceType": "Observation",
        "id": f"ObservationImpression-{subject_id}",
        "status": "preliminary",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "42241-6",
                        "display": "Hospital admission diagnosis Narrative - Reported"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": first_icd_code,
                    "display": first_icd_title
                }
            ],
            "text": impression
        },
        "subject": {
            "reference": f"Patient/{subject_id}"
        },
        "effectiveDateTime": iso_charttime,
        "valueString": impression,
    }

    return observation_resource

def create_icd_mapping(icd_df):
    """
    Creates a dictionary mapping subject IDs to their ICD codes and titles,
    sorted in their original order.
    """
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

