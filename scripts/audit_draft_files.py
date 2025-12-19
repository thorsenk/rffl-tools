#!/usr/bin/env python3
"""
Audit script to compare two RFFL draft data sources:
- Source A: SourceA_rffl_canonicals_drafts_snake_all [Validate Clean SOT_].xlsx
- Source B: RFFL Draft Results (Source B) (1).xlsx
"""

import pandas as pd
from pathlib import Path
from collections import Counter
import sys

def load_all_sheets(filepath, exclude_sheets=None):
    """Load all data sheets from Excel file"""
    if exclude_sheets is None:
        exclude_sheets = ['Sheet1', 'About this file']
    
    xl_file = pd.ExcelFile(filepath)
    all_data = []
    sheet_info = {}
    
    for sheet_name in xl_file.sheet_names:
        if sheet_name in exclude_sheets:
            continue
        
        try:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            # Skip empty or metadata sheets
            if len(df) < 5 or len(df.columns) < 3:
                continue
            
            # Try to identify year from sheet name
            year = None
            try:
                year = int(sheet_name)
            except:
                pass
            
            all_data.append((sheet_name, df, year))
            sheet_info[sheet_name] = {
                'rows': len(df),
                'columns': len(df.columns),
                'year': year
            }
        except Exception as e:
            print(f"  Warning: Could not load sheet '{sheet_name}': {e}")
    
    return all_data, sheet_info

def normalize_source_a(df, year):
    """Normalize Source A DataFrame"""
    # Source A already has normalized columns
    df_norm = df.copy()
    
    # Ensure year column exists
    if 'year' not in df_norm.columns and year:
        df_norm['year'] = year
    
    # Standardize column names
    col_mapping = {
        'team_code': 'team_code',
        'team_full_name': 'team_full_name',
        'player_name': 'player_name',
        'player_NFL_team': 'nfl_team',
        'player_position': 'position',
        'round': 'round',
        'round_pick': 'round_pick',
        'overall_pick': 'overall_pick',
        'is_a_keeper?': 'is_keeper',
        'is_co_owned': 'is_co_owned',
        'owner_code_1': 'owner_1',
        'owner_code_2': 'owner_2',
        'player_id': 'player_id'
    }
    
    # Rename columns
    rename_dict = {k: v for k, v in col_mapping.items() if k in df_norm.columns}
    df_norm = df_norm.rename(columns=rename_dict)
    
    return df_norm

def normalize_source_b(df, year):
    """Normalize Source B DataFrame to match Source A structure"""
    df_norm = df.copy()
    
    # Map Source B columns to Source A structure
    col_mapping = {
        'Draft_Year': 'year',
        'Draft_Round': 'round',
        'Overall_Pick': 'overall_pick',
        'RFFL_Team': 'team_code',
        'Player_Drafted': 'player_name',
        'NFL_Team': 'nfl_team',
        'Position': 'position',
        'Keeper': 'is_keeper'
    }
    
    # Rename columns
    rename_dict = {k: v for k, v in col_mapping.items() if k in df_norm.columns}
    df_norm = df_norm.rename(columns=rename_dict)
    
    # Set year if not present
    if 'year' not in df_norm.columns and year:
        df_norm['year'] = year
    
    # Add missing columns with None
    for col in ['team_full_name', 'round_pick', 'is_co_owned', 'owner_1', 'owner_2', 'player_id']:
        if col not in df_norm.columns:
            df_norm[col] = None
    
    # Normalize keeper column
    if 'is_keeper' in df_norm.columns:
        df_norm['is_keeper'] = df_norm['is_keeper'].astype(str).str.lower().isin(['yes', 'true', '1', 'y', 'keeper'])
    
    return df_norm

def combine_sheets(all_data, normalize_func, source_name):
    """Combine all sheets into single DataFrame"""
    combined = []
    years_found = []
    
    for sheet_name, df, year in all_data:
        try:
            df_norm = normalize_func(df, year)
            combined.append(df_norm)
            if year:
                years_found.append(year)
        except Exception as e:
            print(f"  Warning: Error normalizing {source_name} sheet '{sheet_name}': {e}")
    
    if not combined:
        return None, []
    
    result = pd.concat(combined, ignore_index=True)
    return result, sorted(set(years_found))

def analyze_dataframe(df, name):
    """Analyze a DataFrame and return summary statistics"""
    if df is None or len(df) == 0:
        return None
    
    analysis = {
        'name': name,
        'shape': df.shape,
        'columns': list(df.columns),
        'total_rows': len(df),
        'null_counts': df.isnull().sum().to_dict(),
        'dtypes': df.dtypes.to_dict(),
    }
    
    # Year analysis
    if 'year' in df.columns:
        analysis['years'] = sorted(df['year'].unique())
        analysis['year_counts'] = df['year'].value_counts().to_dict()
        analysis['year_range'] = (int(df['year'].min()), int(df['year'].max()))
    
    # Team analysis
    if 'team_code' in df.columns:
        analysis['unique_teams'] = df['team_code'].nunique()
        analysis['team_counts'] = df['team_code'].value_counts().to_dict()
    
    # Player analysis
    if 'player_name' in df.columns:
        analysis['unique_players'] = df['player_name'].nunique()
        analysis['null_players'] = df['player_name'].isnull().sum()
    
    # Keeper analysis
    if 'is_keeper' in df.columns:
        keeper_count = df['is_keeper'].sum() if df['is_keeper'].dtype == bool else len(df[df['is_keeper'] == True])
        analysis['keeper_count'] = keeper_count
    
    return analysis

def compare_dataframes(df_a, df_b):
    """Compare two normalized DataFrames"""
    comparisons = {}
    
    # Basic structure
    comparisons['row_count_diff'] = len(df_a) - len(df_b)
    
    # Year comparison
    if 'year' in df_a.columns and 'year' in df_b.columns:
        years_a = set(df_a['year'].unique())
        years_b = set(df_b['year'].unique())
        comparisons['year_diff'] = {
            'only_in_a': sorted(years_a - years_b),
            'only_in_b': sorted(years_b - years_a),
            'common': sorted(years_a & years_b)
        }
        
        # Year-by-year row counts
        comparisons['year_counts'] = {}
        all_years = years_a | years_b
        for year in sorted(all_years):
            count_a = len(df_a[df_a['year'] == year]) if year in years_a else 0
            count_b = len(df_b[df_b['year'] == year]) if year in years_b else 0
            comparisons['year_counts'][year] = {
                'source_a': count_a,
                'source_b': count_b,
                'diff': count_a - count_b
            }
    
    # Compare records by key fields
    key_cols = ['year', 'round', 'overall_pick']
    if all(col in df_a.columns for col in key_cols) and all(col in df_b.columns for col in key_cols):
        # Merge on key columns
        merged = pd.merge(
            df_a[key_cols + ['team_code', 'player_name']],
            df_b[key_cols + ['team_code', 'player_name']],
            on=key_cols,
            how='outer',
            indicator=True,
            suffixes=('_a', '_b')
        )
        
        comparisons['merge_analysis'] = {
            'both': len(merged[merged['_merge'] == 'both']),
            'only_in_a': len(merged[merged['_merge'] == 'left_only']),
            'only_in_b': len(merged[merged['_merge'] == 'right_only'])
        }
        
        # Check for mismatches in team/player
        both_records = merged[merged['_merge'] == 'both']
        if len(both_records) > 0:
            team_mismatch = both_records[both_records['team_code_a'] != both_records['team_code_b']]
            player_mismatch = both_records[both_records['player_name_a'] != both_records['player_name_b']]
            
            comparisons['data_mismatches'] = {
                'team_mismatches': len(team_mismatch),
                'player_mismatches': len(player_mismatch)
            }
            
            if len(team_mismatch) > 0:
                comparisons['sample_team_mismatches'] = team_mismatch.head(5)[key_cols + ['team_code_a', 'team_code_b']].to_dict('records')
            if len(player_mismatch) > 0:
                comparisons['sample_player_mismatches'] = player_mismatch.head(5)[key_cols + ['player_name_a', 'player_name_b']].to_dict('records')
    
    return comparisons

def print_analysis(analysis):
    """Print analysis results"""
    if analysis is None:
        return
    
    print(f"\n{'='*80}")
    print(f"ANALYSIS: {analysis['name']}")
    print(f"{'='*80}")
    print(f"Shape: {analysis['shape'][0]:,} rows × {analysis['shape'][1]} columns")
    print(f"\nColumns ({len(analysis['columns'])}):")
    for col in analysis['columns']:
        print(f"  - {col}")
    
    if 'years' in analysis:
        print(f"\nYears: {analysis['years']}")
        print(f"Year Range: {analysis['year_range'][0]} - {analysis['year_range'][1]}")
        print(f"\nYear Distribution:")
        for year in sorted(analysis['year_counts'].keys()):
            print(f"  {year}: {analysis['year_counts'][year]:,} rows")
    
    if 'unique_teams' in analysis:
        print(f"\nUnique Teams: {analysis['unique_teams']}")
    
    if 'unique_players' in analysis:
        print(f"\nUnique Players: {analysis['unique_players']:,}")
        if 'null_players' in analysis and analysis['null_players'] > 0:
            print(f"Null Player Names: {analysis['null_players']}")
    
    if 'keeper_count' in analysis:
        print(f"\nKeeper Picks: {analysis['keeper_count']}")
    
    print(f"\nNull Value Counts (top 10):")
    null_sorted = sorted(analysis['null_counts'].items(), key=lambda x: x[1], reverse=True)
    for col, count in null_sorted[:10]:
        if count > 0:
            pct = (count / analysis['total_rows']) * 100
            print(f"  {col}: {count:,} ({pct:.1f}%)")

def print_comparison(comparison):
    """Print comparison results"""
    print(f"\n{'='*80}")
    print("COMPARISON RESULTS")
    print(f"{'='*80}")
    
    print(f"\nRow Count Difference: {comparison['row_count_diff']:,} (Source A - Source B)")
    
    if 'year_diff' in comparison:
        print(f"\nYear Coverage:")
        if comparison['year_diff']['only_in_a']:
            print(f"  Only in Source A: {comparison['year_diff']['only_in_a']}")
        if comparison['year_diff']['only_in_b']:
            print(f"  Only in Source B: {comparison['year_diff']['only_in_b']}")
        print(f"  Common Years: {len(comparison['year_diff']['common'])}")
        
        print(f"\nYear-by-Year Row Counts:")
        print(f"  {'Year':<6} {'Source A':<12} {'Source B':<12} {'Difference':<12}")
        print(f"  {'-'*6} {'-'*12} {'-'*12} {'-'*12}")
        for year, counts in comparison['year_counts'].items():
            diff_str = f"{counts['diff']:+,}" if counts['diff'] != 0 else "0"
            print(f"  {year:<6} {counts['source_a']:<12,} {counts['source_b']:<12,} {diff_str:<12}")
    
    if 'merge_analysis' in comparison:
        print(f"\nRecord Matching (by year/round/overall_pick):")
        print(f"  Records in both: {comparison['merge_analysis']['both']:,}")
        print(f"  Only in Source A: {comparison['merge_analysis']['only_in_a']:,}")
        print(f"  Only in Source B: {comparison['merge_analysis']['only_in_b']:,}")
        
        if 'data_mismatches' in comparison:
            print(f"\nData Quality Issues:")
            print(f"  Team Code Mismatches: {comparison['data_mismatches']['team_mismatches']:,}")
            print(f"  Player Name Mismatches: {comparison['data_mismatches']['player_mismatches']:,}")
            
            if 'sample_team_mismatches' in comparison:
                print(f"\nSample Team Mismatches (first 5):")
                for record in comparison['sample_team_mismatches']:
                    print(f"  Year {record['year']}, Round {record['round']}, Pick {record['overall_pick']}: "
                          f"Source A='{record['team_code_a']}' vs Source B='{record['team_code_b']}'")
            
            if 'sample_player_mismatches' in comparison:
                print(f"\nSample Player Mismatches (first 5):")
                for record in comparison['sample_player_mismatches']:
                    print(f"  Year {record['year']}, Round {record['round']}, Pick {record['overall_pick']}: "
                          f"Source A='{record['player_name_a']}' vs Source B='{record['player_name_b']}'")

def main():
    repo_root = Path(__file__).parent.parent
    file_a = repo_root / "data" / "teams" / "SourceA_rffl_canonicals_drafts_snake_all [Validate Clean SOT_].xlsx"
    file_b = repo_root / "data" / "teams" / "RFFL Draft Results (Source B) (1).xlsx"
    
    print("="*80)
    print("RFFL DRAFT FILES AUDIT")
    print("="*80)
    
    print("\nLoading Source A...")
    data_a, sheets_a = load_all_sheets(file_a)
    print(f"  Found {len(data_a)} data sheets")
    for sheet, info in sheets_a.items():
        print(f"    {sheet}: {info['rows']} rows, {info['columns']} cols")
    
    print("\nLoading Source B...")
    data_b, sheets_b = load_all_sheets(file_b)
    print(f"  Found {len(data_b)} data sheets")
    for sheet, info in sheets_b.items():
        print(f"    {sheet}: {info['rows']} rows, {info['columns']} cols")
    
    print("\nCombining Source A sheets...")
    df_a, years_a = combine_sheets(data_a, normalize_source_a, "Source A")
    print(f"  Combined: {len(df_a):,} rows across {len(years_a)} years: {years_a}")
    
    print("\nCombining Source B sheets...")
    df_b, years_b = combine_sheets(data_b, normalize_source_b, "Source B")
    print(f"  Combined: {len(df_b):,} rows across {len(years_b)} years: {years_b}")
    
    if df_a is None or df_b is None:
        print("\nError: Could not combine data from one or both files")
        sys.exit(1)
    
    print("\nAnalyzing Source A...")
    analysis_a = analyze_dataframe(df_a, "Source A")
    print_analysis(analysis_a)
    
    print("\nAnalyzing Source B...")
    analysis_b = analyze_dataframe(df_b, "Source B")
    print_analysis(analysis_b)
    
    print("\nComparing files...")
    comparison = compare_dataframes(df_a, df_b)
    print_comparison(comparison)
    
    print(f"\n{'='*80}")
    print("AUDIT COMPLETE")
    print(f"{'='*80}")
    
    # Summary recommendations
    print("\nSUMMARY & RECOMMENDATIONS:")
    print("-" * 80)
    
    if comparison['row_count_diff'] != 0:
        print(f"⚠️  Row count mismatch: {abs(comparison['row_count_diff']):,} row difference")
    
    if 'year_diff' in comparison:
        if comparison['year_diff']['only_in_a']:
            print(f"⚠️  Source A has years not in Source B: {comparison['year_diff']['only_in_a']}")
        if comparison['year_diff']['only_in_b']:
            print(f"⚠️  Source B has years not in Source A: {comparison['year_diff']['only_in_b']}")
    
    if 'merge_analysis' in comparison:
        match_rate = (comparison['merge_analysis']['both'] / max(len(df_a), len(df_b))) * 100
        print(f"✓ Record match rate: {match_rate:.1f}%")
        
        if comparison['merge_analysis']['only_in_a'] > 0:
            print(f"⚠️  {comparison['merge_analysis']['only_in_a']:,} records only in Source A")
        if comparison['merge_analysis']['only_in_b'] > 0:
            print(f"⚠️  {comparison['merge_analysis']['only_in_b']:,} records only in Source B")
    
    if 'data_mismatches' in comparison:
        if comparison['data_mismatches']['team_mismatches'] > 0:
            print(f"⚠️  {comparison['data_mismatches']['team_mismatches']:,} team code mismatches")
        if comparison['data_mismatches']['player_mismatches'] > 0:
            print(f"⚠️  {comparison['data_mismatches']['player_mismatches']:,} player name mismatches")

if __name__ == "__main__":
    main()
