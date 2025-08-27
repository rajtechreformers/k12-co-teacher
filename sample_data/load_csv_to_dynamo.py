#!/usr/bin/env python3
"""
Load CSV files from dynamo_data/ folder into DynamoDB tables.
Handles the specific data format used in the K-12 Co-Teacher project.
"""

import boto3
import csv
import json
import os
from decimal import Decimal

def json_loads_decimal(s):
    """Parse JSON with Decimal support for DynamoDB"""
    return json.loads(s, parse_float=Decimal)

def clean_dynamo_format(value):
    """Clean DynamoDB format strings like {"S":"value"} to just "value" """
    if isinstance(value, str):
        try:
            # Try to parse as JSON first
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                # Handle DynamoDB format objects
                result = {}
                for k, v in parsed.items():
                    if isinstance(v, dict) and 'S' in v:
                        result[k] = v['S']
                    else:
                        result[k] = v
                return result
            elif isinstance(parsed, list):
                # Handle arrays of DynamoDB format
                result = []
                for item in parsed:
                    if isinstance(item, dict) and 'S' in item:
                        result.append(item['S'])
                    else:
                        result.append(item)
                return result
            return parsed
        except (json.JSONDecodeError, ValueError):
            return value
    return value

def load_csv_to_table(table_name, csv_file_path, dry_run=False):
    """Load CSV data into a DynamoDB table"""
    if not dry_run:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
    
    action = "DRY RUN - Would load" if dry_run else "Loading"
    print(f"{action} {csv_file_path} into {table_name}...")
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        items_processed = 0
        if not dry_run:
            with table.batch_writer() as batch:
                for row in csv_reader:
                    # Clean up the data
                    item = {}
                    for key, value in row.items():
                        if value:  # Skip empty values
                            cleaned_value = clean_dynamo_format(value)
                            item[key] = cleaned_value
                    
                    # Put item into DynamoDB
                    batch.put_item(Item=item)
                    items_processed += 1
                    print(f"  Added item with key: {list(item.keys())[0]}={list(item.values())[0]}")
        else:
            # Dry run - just process and show what would be loaded
            for row in csv_reader:
                item = {}
                for key, value in row.items():
                    if value:
                        cleaned_value = clean_dynamo_format(value)
                        item[key] = cleaned_value
                
                items_processed += 1
                print(f"  Would add: {list(item.keys())[0]}={list(item.values())[0]}")
                if items_processed <= 3:  # Show first 3 items in detail
                    print(f"    Full item: {item}")
    
    status = "Would complete" if dry_run else "Completed"
    print(f"{status} loading {table_name} ({items_processed} items)\n")

def main():
    """Load all CSV files in dynamo_data/ folder"""
    import sys
    
    # Check for dry run flag
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dynamo_data_dir = os.path.join(script_dir, 'dynamo_data')
    
    if not os.path.exists(dynamo_data_dir):
        print(f"Directory not found: {dynamo_data_dir}")
        return
    
    # Map CSV files to table names
    csv_files = [
        'k12-coteacher-teachers-to-classes.csv',
        'k12-coteacher-class-attributes.csv', 
        'k12-coteacher-class-to-students.csv',
        'k12-coteacher-student-profiles.csv'
    ]
    
    mode = "DRY RUN MODE" if dry_run else "LIVE MODE"
    print(f"Starting DynamoDB data load - {mode}\n")
    
    if dry_run:
        print("DRY RUN: No data will be written to DynamoDB\n")
    
    for csv_file in csv_files:
        csv_path = os.path.join(dynamo_data_dir, csv_file)
        
        if os.path.exists(csv_path):
            # Extract table name from filename (remove .csv extension)
            table_name = csv_file.replace('.csv', '')
            
            try:
                load_csv_to_table(table_name, csv_path, dry_run=dry_run)
            except Exception as e:
                print(f"Error loading {csv_file}: {e}\n")
        else:
            print(f"File not found: {csv_path}")
    
    if dry_run:
        print("Dry run complete! Run without --dry-run to actually load data.")
    else:
        print("Data loading complete!")

if __name__ == "__main__":
    main()