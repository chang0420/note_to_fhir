# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 17:23:40 2025

@author: user
"""

import pandas as pd
from google.colab import drive
import json



def format_discharge_medications(df, dischargetime):
    text_output = ["DISCHARGE MEDICATIONS:"]
    unique_df = df.drop_duplicates(subset=["drug"])
    dischargetime_value = dischargetime.iloc[0].split()[0]

    num = 0
    for _, row in unique_df.iterrows():
        end_date = row['enddate'].split()[0] if pd.notna(row['enddate']) else None
        if end_date == dischargetime_value:
            num += 1
            text_output.append(f"{num}. {row['drug']} {row['dose_val_rx']} {row['dose_unit_rx']} {row['route']}.")

    return "\n".join(text_output)


def create_fhir_medication_request(df, dischargetime):
    fhir_resources = []
    unique_df = df.drop_duplicates(subset=["drug"])
    dischargetime_value = dischargetime.iloc[0].split()[0]

    for _, row in unique_df.iterrows():
        end_date = row['enddate'].split()[0] if pd.notna(row['enddate']) else None
        if end_date == dischargetime_value:
            medication_request = {
                "resourceType": "MedicationRequest",
                "id": f"MedicationRequest-{row['row_id']}",
                "status": "active",
                "intent": "order",
                "medicationCodeableConcept": {
                    "coding": [
                        {
                            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                            "code": row["formulary_drug_cd"],
                            "display": row["drug"]
                        }
                    ],
                    "text": row["drug"]
                },
                "subject": {"reference": f"Patient/{row['subject_id']}"},
                "encounter": {"reference": f"Encounter/{row['hadm_id']}"},
                "authoredOn": dischargetime_value,
                "dosageInstruction": [
                    {
                        "text": f"{row['dose_val_rx']} {row['dose_unit_rx']} {row['route']}",
                        "route": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/route-of-administration",
                                    "code": row["route"],
                                    "display": row["route"]
                                }
                            ]
                        },
                        "doseAndRate": [
                            {
                                "doseQuantity": {
                                    "value": row["dose_val_rx"],
                                    "unit": row["dose_unit_rx"],
                                    "system": "http://unitsofmeasure.org",
                                    "code": row["dose_unit_rx"]
                                }
                            }
                        ]
                    }
                ]
            }
            fhir_resources.append(medication_request)

    return fhir_resources

