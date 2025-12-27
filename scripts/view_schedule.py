#!/usr/bin/env -S uv run python
"""
View and calculate planting schedule with date dependencies.
"""

import pandas as pd
from datetime import datetime, timedelta

def calculate_prep_dates(df):
    """Calculate prep_start_date based on target_date and prep_duration_weeks."""
    df = df.copy()

    # Convert target_date to datetime
    df['target_date'] = pd.to_datetime(df['target_date'])

    # Calculate prep_start_date where prep_duration_weeks is provided
    mask = df['prep_duration_weeks'].notna()
    df.loc[mask, 'calculated_prep_start'] = df.loc[mask].apply(
        lambda row: row['target_date'] - timedelta(weeks=row['prep_duration_weeks']),
        axis=1
    )

    # Compare with manual prep_start_date if provided
    df['prep_start_date'] = pd.to_datetime(df['prep_start_date'], errors='coerce')

    return df

def main():
    # Load schedule
    schedule_file = 'data/schedules/planting_schedule.csv'
    df = pd.read_csv(schedule_file)

    # Calculate dates
    df = calculate_prep_dates(df)

    # Format for display
    display_df = df[[
        'task_type', 'crop', 'target_date',
        'prep_method', 'prep_duration_weeks',
        'calculated_prep_start', 'notes'
    ]].copy()

    # Format dates nicely
    display_df['target_date'] = pd.to_datetime(display_df['target_date']).dt.strftime('%Y-%m-%d (%a)')
    display_df['calculated_prep_start'] = display_df['calculated_prep_start'].dt.strftime('%Y-%m-%d (%a)')

    print("\n=== Happy Farm Planting Schedule ===\n")
    print(display_df.to_string(index=False))
    print("\n")

    # Show upcoming tasks (within next 60 days)
    today = datetime.now()
    upcoming = df[
        (df['calculated_prep_start'] >= today) &
        (df['calculated_prep_start'] <= today + timedelta(days=60))
    ].sort_values('calculated_prep_start')

    if not upcoming.empty:
        print("=== Upcoming Tasks (Next 60 Days) ===\n")
        for _, row in upcoming.iterrows():
            days_until = (row['calculated_prep_start'] - today).days
            print(f"📅 {row['calculated_prep_start'].strftime('%Y-%m-%d')} ({days_until} days)")
            print(f"   {row['task_type']}: {row['crop']}")
            print(f"   Method: {row['prep_method']} ({row['prep_duration_weeks']} weeks)")
            print(f"   Target: {row['target_date'].strftime('%Y-%m-%d')}")
            print(f"   Notes: {row['notes']}\n")

if __name__ == '__main__':
    main()
