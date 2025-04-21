# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 16:21:48 2025

@author: user
"""
from datetime import datetime



def create_procedure(row):
    subject_id = row['subject_id']
    procedure_icd = row['icd9_code']
    procedure = str(row['long_title'])
    procedure = procedure.replace("\n", " ")
    now = datetime.now()
    iso_charttime = now.isoformat()


    procedure_resource = {
        "resourceType": "Procedure",
        "id": f"Procedure-{subject_id}", 
        "status": "completed",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8724-7",
                        "display": "Surgical operation note description Narrative"

                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "https://twcore.mohw.gov.tw/ig/twcore/CodeSystem/icd-10-pcs-2021-tw",
                    "code": procedure_icd,
                    "display": procedure
                }
            ],
            "text": procedure
        },
        "subject": {
            "reference": f"Patient/{subject_id}"
        },
        "encounter": {
            "reference": f"Encounter/{subject_id}"
        },
        "effectiveDateTime": iso_charttime,

    }

    return procedure_resource


