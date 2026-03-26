# Tenant Review Performance Monitor

A portfolio project that translates a real Excel-based tenant review workflow into a focused Streamlit decision-support app.

## Overview

This project began as an internal spreadsheet system used to monitor tenant performance through customer reviews from Google and Yelp. The original Excel prototype included scorecards, trend analysis, platform comparisons, and GPT-assisted summaries, but it was not suitable for external presentation.

I rebuilt the workflow as a lean Streamlit app to demonstrate how messy operational analysis can be turned into a cleaner, more usable product.

## What the app does

- Lets the user select a tenant from a searchable list
- Displays key business health indicators such as:
  - average rating
  - review count
  - platform rating gap
  - negative review rate
  - risk level
- Shows rating trends over time
- Tracks negative review volume over time
- Compares Google and Yelp performance
- Generates a concise AI-assisted summary of customer sentiment and operational risk

## Why I built it this way

Rather than recreate every feature from the original workbook, I intentionally narrowed the scope to the parts that most clearly communicate performance and risk.

The goal was not to build a larger dashboard. The goal was to build a tighter one.

Key product decisions:
- simplified the original spreadsheet logic into a cleaner data model
- separated raw reviews, business-level KPIs, and yearly aggregates
- limited the app to a small number of charts
- treated AI summarization as a supporting insight layer rather than the main feature
- anonymized business identities and removed proprietary context for public presentation

## Data model

The app uses three CSV files:

- `reviews.csv`  
  Review-level data used for sampling, filtering, and AI summaries

- `businesses.csv`  
  Business-level KPI table used for the selector and scorecards

- `yearly_metrics.csv`  
  Aggregated business-by-year platform metrics used for trend charts

## Tech stack

- Python
- Streamlit
- pandas
- Plotly
- OpenAI API

## Files

- `app.py` - main Streamlit app
- `businesses.csv` - business-level KPI dataset
- `reviews.csv` - anonymized review-level dataset
- `yearly_metrics.csv` - aggregated yearly metrics
- `requirements.txt` - Python dependencies

## Running locally

Create and activate a virtual environment if you want, then install dependencies:

```bash
pip install -r requirements.txt