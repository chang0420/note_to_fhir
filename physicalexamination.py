# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 15:16:17 2025

@author: user
"""

import pandas as pd
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel, BartForConditionalGeneration, BartTokenizer
from sklearn.cluster import KMeans
import re
import builtins
from datetime import datetime
import json

model_name = "emilyalsentzer/Bio_ClinicalBERT"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def physical_exam_frist(pt_notes):
    subject_id = pt_notes["subject_id"]
    global echo_keywords
    echo_keywords = [
        "test information", "indication", "height: (in)", "weight (lb)", "bsa (m2)",
        "bp (mm hg)", "status", "date/time", "test",
        "doppler", "contrast", "technical quality", "findings", "conclusions", "impression", "plan"
    ]

    echo_key_info = extract_echo_key_info(pt_notes, tokenizer, model)
    echo_summary, echo_data = generate_echo_summary(echo_key_info)
    fhir_physical_exams_data = []
    for record in echo_data:
        key_info = record.get("key_info", {})
        indication = key_info.get("indication", "no Indication")
        findings = key_info.get("findings", "no Findings")

        fhir_resource = create_fhir_physical_exam(subject_id, indication, findings)
        fhir_physical_exams_data.append(fhir_resource)
        
    return fhir_physical_exams_data
    

def create_fhir_physical_exam(pt_id, indication, findings):
    now = datetime.now()
    iso_charttime = now.isoformat()

    # 理學檢查
    physical_exam_resource = {
        "resourceType": "Observation",
        "id": f"PhysicalExam-{pt_id}",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "exam",
                        "display": "Physical Examination"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system" : "http://snomed.info/sct",
                    "code": "34728-9",
                    "display": "Echocardiography physical exam findings"
                }
            ],
            "text": indication
        },
        "subject": {
            "reference": f"Patient/{pt_id}"
        },
        "effectiveDateTime": iso_charttime,
        "valueString": findings
    }

    return physical_exam_resource

def extract_specific_keywords(text, keywords):
    lower_text = text.lower()
    positions = []

    for keyword in keywords:
        pattern = re.compile(re.escape(keyword.lower()))
        match = pattern.search(lower_text)
        if match:
            positions.append((match.start(), keyword))

    if not positions:
        return {}

    positions.sort()
    positions.append((len(text), "END"))

    extracted_info = {}

    for i in range(len(positions) - 1):
        start_idx = positions[i][0]
        end_idx = positions[i+1][0]
        keyword = positions[i][1]
        segment = text[start_idx:end_idx].strip()

        cleaned_segment = re.sub(re.escape(keyword), '', segment, flags=re.IGNORECASE).strip()

        if cleaned_segment:
            extracted_info[keyword] = cleaned_segment

    return extracted_info



def split_into_paragraphs(text, max_tokens=300): #512
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n|\r\n\s*\r\n', text) if p.strip()]
    result = []
    for para in paragraphs:
        tokens = tokenizer.tokenize(para)
        if len(tokens) <= max_tokens:
            result.append(para)
        else:
            sentences = [s.strip() for s in re.split(r'[.!?]\s+', para) if s.strip()]
            current = ""
            for sentence in sentences:
                if len(tokenizer.tokenize(current + sentence)) <= max_tokens:
                    current += " " + sentence if current else sentence
                else:
                    if current:
                        result.append(current)
                    current = sentence
            if current:
                result.append(current)

    return result

def extract_echo_key_info(notes, tokenizer, model):
    results = []

    for idx, row in notes.iterrows():
        note_text = row["cleaned_text"]
        charttime = row["charttime"]
        row_id = row["row_id"]

        paragraphs = split_into_paragraphs(note_text)

        if len(paragraphs) <= 3:
            results.append({
                "row_id": row_id,
                "charttime": charttime,
                "key_paragraphs": paragraphs,
                "key_info": extract_specific_keywords(note_text, echo_keywords)
            })
            continue

        paragraph_embeddings = get_embeddings(paragraphs, tokenizer, model)
        relevance_matrix = compute_keyword_relevance(paragraphs, echo_keywords, tokenizer, model)

        key_info = {}
        for i, keyword in enumerate(echo_keywords):
            most_relevant_idx = np.argmax(relevance_matrix[:, i])
            key_info[keyword] = paragraphs[most_relevant_idx]

        precise_key_info = extract_specific_keywords(note_text, echo_keywords)

        for keyword in echo_keywords:
            if keyword in precise_key_info:
                key_info[keyword] = precise_key_info[keyword]

        representative_paragraphs = select_representative_paragraphs(
            paragraph_embeddings, paragraphs, n_clusters=3
        )

        results.append({
            "row_id": row_id,
            "charttime": charttime,
            "key_paragraphs": representative_paragraphs,
            "key_info": key_info
        })

    return results

def generate_echo_summary(key_info_results):
    summary = ["echo Record Summary"]
    echo_data = []

    for i, record in enumerate(key_info_results):
        try:
            charttime = record.get("charttime", "N/A")
            row_id = record.get("row_id", "N/A")
            key_info = record.get("key_info", {})

            summary.append(f"\nRecord {i+1} - Time: {charttime}")

            if not key_info:
                summary.append("* not found!")
                continue

            record_texts = []
            if isinstance(key_info, dict):
                for keyword, text in key_info.items():
                    clean_text = str(text).replace(":", "", 1).strip() if text else "無詳細資訊"
                    summary.append(f"* {keyword}: {clean_text}")
                    record_texts.append(f"{keyword}: {clean_text}")

            echo_data.append({
                "row_id": row_id,
                "charttime": charttime,
                "key_info": key_info,
                "text": "\n".join(record_texts)
            })

        except Exception as e:
            summary.append(f"* 處理記錄 {i+1} 時發生錯誤: {str(e)}")

    return "\n".join(summary), echo_data

