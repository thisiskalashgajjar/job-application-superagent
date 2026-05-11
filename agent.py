#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent.py
Created and coded by Kalash Tejendra Gajjar.
Copyrights to Kalash Tejendra Gajjar

"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_community.tools import DuckDuckGoSearchRun
from database import log_application

load_dotenv()

llm = ChatAnthropic(model="claude-sonnet-4-5", max_tokens=2000)
search_tool = DuckDuckGoSearchRun()

# Job Search

def job_search_agent(state):
    interests = state["interests"]
    location = state["location"]
    
    query = (
        f"software developer {' '.join(interests)} jobs {location} "
        f"2025 site:linkedin.com OR site:indeed.ca OR site:glassdoor.ca"
    )
    print(f"[Agent 1] Searching: {query}")
    raw = search_tool.run(query)
    
    response = llm.invoke(
        f"""From these job search results, extract up to 5 real job postings.
Return ONLY a valid JSON array, no explanation, no markdown.
Format: [{{"title":"","company":"","description":"","url":""}}]

Search results:
{raw}"""
    )

    try:
        jobs = json.loads(response.content)
    except Exception:
        # Fallback: try to extract JSON from response
        content = response.content
        start = content.find("[")
        end   = content.rfind("]") + 1
        try:
            jobs = json.loads(content[start:end])
        except Exception:
            jobs = []

    print(f"[Agent 1] Found {len(jobs)} jobs")
    state["jobs"] = jobs
    return state

# JD Analyzer
def jd_analyzer_agent(state):
    analyzed = []
    for job in state['jobs']:
        print(f"[Agent 2] Analyzing: {job.get('title')} @ {job.get('company')}")
        response = llm.invoke(
            f"""Analyze this job description. Return ONLY valid JSON, no markdown.
            Format: {{"key_skills":[], "keywords": [], "tone":"", "seniority_level":""}}
            
            Job title: {job.get('title', '')}
            Job description: {job.get('description', '')}"""
            )
        try:
            job['analysis'] = json.loads(response.content)
        except Exception:
            job['analysis'] = {"key_skills": [], "keywords": [], "tone": "professional"}
        analyzed.append(job)
    
    state["jobs"] = analyzed
    return state

# Resume Tailor

def resume_agent(state):
    for job in state["jobs"]:
        print(f"[Agent 3] Tailoring resume for: {job.get('title')}")
        analysis = job.get("analysis", {})
        response = llm.invoke(
            f"""You are an expert resume writer for Canadian tech jobs.
Tailor this resume for the specific role below.
- Reorder bullet points to surface the most relevant experience first
- Adjust the summary sentence to reference the role
- Weave in ATS keywords naturally — do not stuff
- Keep all facts truthful, only reframe
- Output the full resume as plain text

Master Resume:
{state['resume_text']}

Target Role: {job.get('title','')} at {job.get('company','')}
Key Skills Required: {analysis.get('key_skills',[])}
ATS Keywords: {analysis.get('keywords',[])}
"""
        )
        job["tailored_resume"] = response.content
    return state

# Cover Letter

def cover_letter_agent(state):
    for job in state["jobs"]:
        print(f"[Agent 4] Writing cover letter for: {job.get('title')}")
        analysis = job.get("analysis", {})
        response = llm.invoke(
            f"""Write a professional, concise cover letter for a Canadian job application.

Applicant: Kalash Gajjar
- Recent graduate, Centennial College, Advanced Diploma in Software Engineering Technology – AI
- GPA 3.97/4.5, based in Toronto ON
- Skills: Python, Java, TensorFlow, scikit-learn, AWS, React, SQL

Role: {job.get('title','')} at {job.get('company','')}
Required Skills: {analysis.get('key_skills',[])}
Tone: {analysis.get('tone','professional')}

Rules:
- Under 350 words
- First person, confident, no generic filler
- Reference 2-3 specific skills from the job naturally
- End with a clear call to action
"""
        )
        job["cover_letter"] = response.content

        # Log to database immediately
        log_application(
            job_title    = job.get("title", "Unknown"),
            company      = job.get("company", "Unknown"),
            url          = job.get("url", ""),
            resume       = job["tailored_resume"],
            cover_letter = job["cover_letter"],
            applied_at   = datetime.now().isoformat()
        )
        print(f"[Agent 4] Logged application for {job.get('title')}")

    state["status"] = "done"
    return state

# Build LangGraph

def build_graph():
    g = StateGraph(dict)
    g.add_node("search",       job_search_agent)
    g.add_node("analyze",      jd_analyzer_agent)
    g.add_node("resume",       resume_agent)
    g.add_node("cover_letter", cover_letter_agent)

    g.set_entry_point("search")
    g.add_edge("search",       "analyze")
    g.add_edge("analyze",      "resume")
    g.add_edge("resume",       "cover_letter")
    g.add_edge("cover_letter", END)
    return g.compile()

graph = build_graph()

def run_job_agent(interests, location, resume_text):
    result = graph.invoke({
        "interests":   interests,
        "location":    location,
        "resume_text": resume_text,
        "jobs":        [],
        "status":      "running"
    })
    return result["jobs"]

