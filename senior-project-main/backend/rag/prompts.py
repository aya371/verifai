from typing import List, Dict

def build_fact_check_prompt(claim: str, evidence_chunks: List[Dict], language: str = "English") -> str:
    """
    Build RAG prompt for Claude fact-checking
    Supports multilingual reasoning output.
    """
    evidence_text = ""
    for i, chunk in enumerate(evidence_chunks, 1):
        evidence_text += f"""
[Source {i}]
Text: {chunk['text']}
Source: {chunk['source']}
Date: {chunk['date']}
Credibility: {chunk['credibility']:.2f}
---
"""
    language_instruction = (
        f"8. Write your 'reasoning' field in {language}."
        if language != "English"
        else ""
    )

    prompt = f"""You are a fact-checking agent for the VerifAI system. Your task is to verify the following claim using ONLY the provided evidence sources.

CLAIM TO VERIFY:
"{claim}"

RETRIEVED EVIDENCE:
{evidence_text}

CRITICAL INSTRUCTIONS:
1. Analyze the claim against each evidence source
2. Determine if the claim is SUPPORTED, REFUTED, or INCONCLUSIVE
3. Provide a confidence score (0-100%)
4. Cite specific evidence sources ([Source 1], [Source 2], etc.) in your reasoning
5. DO NOT use any knowledge outside the provided sources
6. If the evidence is insufficient, respond with "INCONCLUSIVE"
7. If sources contradict each other, note this in your reasoning
{language_instruction}

RESPONSE FORMAT (JSON ONLY):
{{
    "verdict": "SUPPORTED" | "REFUTED" | "INCONCLUSIVE",
    "confidence": 0-100,
    "reasoning": "Detailed explanation citing [Source 1], [Source 2], etc. Written in {language}.",
    "flags": ["contradictory_sources", "low_credibility_source", etc.]
}}

Respond with ONLY the JSON object, no additional text.
"""
    return prompt
