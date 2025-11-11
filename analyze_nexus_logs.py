#!/usr/bin/env python3
"""
Analyze Nexus repository access logs by package format
Usage: python3 analyze_nexus_logs.py /path/to/nexus.log
"""

import re
import sys
from collections import Counter, defaultdict

def categorize_repo(repo_name):
    """Categorize repository by package format based on name"""
    repo_lower = repo_name.lower()
    
    if 'maven' in repo_lower:
        return 'Maven'
    elif 'npm' in repo_lower:
        return 'npm'
    elif 'docker' in repo_lower:
        return 'Docker'
    elif 'nuget' in repo_lower:
        return 'NuGet'
    elif 'pypi' in repo_lower or 'python' in repo_lower:
        return 'PyPI'
    elif 'p2' in repo_lower or 'eclipse' in repo_lower:
        return 'P2/Eclipse'
    else:
        return 'Other'

def analyze_logs(logfile):
    """Analyze Nexus logs and count requests by repository and format"""
    
    # Pattern to extract repository name from: GET /repository/REPO_NAME/
    pattern = re.compile(r'GET /repository/([^/]+)/')
    
    # Pattern to extract IP address (first field in log line)
    ip_pattern = re.compile(r'^(\S+)')
    
    repo_counter = Counter()
    format_counter = defaultdict(int)
    ip_format_counter = defaultdict(Counter)  # format -> {ip: count}
    
    print(f"Analyzing: {logfile}")
    print("Processing...", end='', flush=True)
    
    with open(logfile, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 100000 == 0:
                print('.', end='', flush=True)
            
            match = pattern.search(line)
            if match:
                repo_name = match.group(1)
                repo_counter[repo_name] += 1
                
                # Categorize by format
                format_type = categorize_repo(repo_name)
                format_counter[format_type] += 1
                
                # Extract IP address
                ip_match = ip_pattern.match(line)
                if ip_match:
                    ip_address = ip_match.group(1)
                    ip_format_counter[format_type][ip_address] += 1
    
    print(" Done!\n")
    
    return repo_counter, format_counter, ip_format_counter

def print_results(repo_counter, format_counter, ip_format_counter):
    """Print analysis results"""
    
    total = sum(repo_counter.values())
    
    # Print by repository
    print("="*60)
    print("REPOSITORY ACCESS BREAKDOWN")
    print("="*60)
    print(f"{'Requests':>10} | {'Repository'}")
    print("-"*60)
    
    for repo, count in repo_counter.most_common():
        print(f"{count:>10,} | {repo}")
    
    print("-"*60)
    print(f"{total:>10,} | TOTAL\n")
    
    # Print by format
    print("="*60)
    print("PACKAGE FORMAT SUMMARY")
    print("="*60)
    print(f"{'Requests':>10} | {'Percentage':>10} | {'Format'}")
    print("-"*60)
    
    # Sort by request count (descending)
    sorted_formats = sorted(format_counter.items(), key=lambda x: x[1], reverse=True)
    
    for format_type, count in sorted_formats:
        percentage = (count / total * 100) if total > 0 else 0
        print(f"{count:>10,} | {percentage:>9.2f}% | {format_type}")
    
    print("-"*60)
    print(f"{total:>10,} | {100.0:>9.2f}% | TOTAL\n")
    
    # Print top 3 clients per format
    print("="*60)
    print("TOP 3 CLIENTS PER PACKAGE FORMAT")
    print("="*60)
    
    for format_type, count in sorted_formats:
        if count > 0:
            print(f"\n{format_type}:")
            print(f"  {'Rank'} | {'Requests':>10} | {'IP Address'}")
            print(f"  {'-'*4} | {'-'*10} | {'-'*18}")
            
            # Get top 3 IPs for this format
            top_ips = ip_format_counter[format_type].most_common(3)
            
            for rank, (ip, ip_count) in enumerate(top_ips, 1):
                print(f"     {rank} | {ip_count:>10,} | {ip}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_nexus_logs.py /path/to/nexus.log")
        sys.exit(1)
    
    logfile = sys.argv[1]
    
    try:
        repo_counter, format_counter, ip_format_counter = analyze_logs(logfile)
        print_results(repo_counter, format_counter, ip_format_counter)
        
    except FileNotFoundError:
        print(f"Error: File '{logfile}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
