# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 16:28:57 2025

@author: user
"""

import csv
import json
from datetime import datetime
import ast
import pandas as pd

def create_text_observation(row, icd_mapping):
    subject_id = row['SUBJECT_ID']
    hadm_id = row['HADM_ID']
    row_id = row['ROW_ID']
    charttime = row['CHARTTIME']


    try:
        key_info = json.loads(row['KEY_INFO'])
    except json.JSONDecodeError:
        key_info = ast.literal_eval(row['KEY_INFO'])
        print(f"Decoding JSON in row {row_id}: {row['KEY_INFO']}")
    text = key_info.get("findings", "")
    if not text:
        text = key_info.get("impression", "")

    iso_charttime = datetime.strptime(charttime, "%Y-%m-%d %H:%M:%S").isoformat()
    first_icd_code = ""
    first_icd_title = ""
    subject_id_str = str(subject_id)

    if subject_id_str in icd_mapping and icd_mapping[subject_id_str]:
        first_icd_code = icd_mapping[subject_id_str][0]['icd9_code']
        first_icd_title = icd_mapping[subject_id_str][0]['long_title']
    else:
        print(f"No ICD codes found for subject {subject_id}")

    condition_resource = {
        "resourceType": "ImagingStudy",
        "id": f"ImagingStudy-{subject_id}",
        "status": "available",
        "subject": {
            "reference": f"Patient/{subject_id}"
        },
        "encounter": {
            "reference": f"Encounter/{subject_id}"
        },
        "started": iso_charttime,
        "interpreter": [#醫師資料
            {
                "reference": "Practitioner/Practitioner-min"
            }
        ],
        "despcription": text
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

