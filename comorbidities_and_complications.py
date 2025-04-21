# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 19:36:55 2025

@author: user
"""

import re
import pandas as pd


def create_comorbidities_and_complications(icd_code, diagnoses):

    icd_code = icd_code.replace('\r\n', '').strip()
    now = datetime.now()
    iso_charttime = now.isoformat()


    condition_resource = {
        "resourceType": "Condition",
        "id": f"Condition-{subject_id}", 
         "clinicalStatus" : {
          "coding" : [
            {
              "system" : "http://terminology.hl7.org/CodeSystem/condition-clinical",
              "code" : "resolved",
              "display" : "Resolved"
            }
          ],
          "text" : "解決"
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "555109-3",
                        "display": "Complications Document"

                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "https://twcore.mohw.gov.tw/ig/twcore/CodeSystem/icd-10-pcs-2021-tw",
                    "code": icd_code,
                    "display": diagnoses
                }
            ],
            "text": diagnoses
        },
        "subject": {
            "reference": f"Patient/{subject_id}"
        },
        "encounter": {
            "reference": f"Encounter/{subject_id}" 
        },
        "recordedDateTime": iso_charttime,

    }

    return condition_resource


def normalize_comorbidity(comorb):
    return comorb.replace('\\r', '').strip()


def map_comorbidities_to_icd9(comorbidities, mapping_df):
    mapping_results = {}
    for comorb in comorbidities:
        norm_comorb = normalize_comorbidity(comorb)
        #print(norm_comorb)
        matches = mapping_df[mapping_df['Comorbidities'].str.lower().str.contains(norm_comorb.lower(), na=False)]
        if not matches.empty:
            mapping_results[norm_comorb] = matches.iloc[0]['Enhanced ICD-9-CM']
        else:
            mapping_results[norm_comorb] = None
    return mapping_results


