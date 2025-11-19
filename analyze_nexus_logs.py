#!/usr/bin/env python3
"""
Analyze Nexus repository access logs by package format
Usage: python3 analyze_nexus_logs.py /path/to/nexus.log
"""

import re
import sys
from collections import Counter, defaultdict

def get_format_rules():
    """
    Returns detection rules for each package format.

    Customize this function to add new formats or modify detection patterns.
    Each format has three types of detection patterns (checked in order):
    - user_agents: Patterns in the User-Agent string (highest confidence)
    - file_patterns: File extensions or specific filenames in the request path
    - repo_patterns: Keywords in the repository name (lowest confidence)
    """
    return {
        'Maven': {
            'user_agents': ['Apache-Maven', 'maven'],
            'file_patterns': ['maven-metadata.xml', '.pom', '.jar', '.war', '.ear'],
            'repo_patterns': ['maven', 'snapshots', 'releases']
        },
        'npm': {
            'user_agents': ['npm/', 'yarn/', 'pnpm/'],
            'file_patterns': ['package.json', '.tgz', '/-/'],
            'repo_patterns': ['npm']
        },
        'Docker': {
            'user_agents': ['docker/', 'containerd/'],
            'file_patterns': ['/v2/', '/manifests/', '/blobs/'],
            'repo_patterns': ['docker']
        },
        'NuGet': {
            'user_agents': ['NuGet'],
            'file_patterns': ['.nupkg', '.nuspec', '/Packages('],
            'repo_patterns': ['nuget']
        },
        'PyPI': {
            'user_agents': ['pip/', 'twine/', 'python-requests'],
            'file_patterns': ['.whl', '.egg', '/simple/', '/packages/'],
            'repo_patterns': ['pypi', 'python']
        },
        'P2/Eclipse': {
            'user_agents': ['p2/', 'Eclipse'],
            'file_patterns': ['content.jar', 'artifacts.jar', '.jar'],
            'repo_patterns': ['p2', 'eclipse']
        }
    }

def categorize_request(repo_name, user_agent, request_path):
    """
    Categorize request by package format using hybrid detection.

    Uses multiple signals in priority order:
    1. User-Agent string (most reliable)
    2. File patterns in request path
    3. Repository name patterns (fallback)

    Stops at the first match for efficiency.
    """
    rules = get_format_rules()
    repo_lower = repo_name.lower()
    user_agent_lower = user_agent.lower()
    path_lower = request_path.lower()

    # Try each format in order
    for format_name, format_rules in rules.items():
        # Check user-agent first (highest confidence)
        if any(ua.lower() in user_agent_lower for ua in format_rules['user_agents']):
            return format_name

        # Check file patterns second
        if any(pattern.lower() in path_lower for pattern in format_rules['file_patterns']):
            return format_name

        # Check repo name last (lowest confidence)
        if any(pattern.lower() in repo_lower for pattern in format_rules['repo_patterns']):
            return format_name

    return 'Other'

def analyze_logs(logfile):
    """Analyze Nexus logs and count requests by repository and format"""

    # Pattern to extract request details from log line
    # Format: IP - - [timestamp] "METHOD /repository/REPO_NAME/PATH HTTP/VERSION" status - bytes time "USER-AGENT" [thread]
    request_pattern = re.compile(r'"([A-Z]+) (/repository/([^/]+)/[^\s]*) HTTP/[^"]*"\s+\d+\s+\S+\s+\S+\s+\S+\s+"([^"]*)"')

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

            match = request_pattern.search(line)
            if match:
                method = match.group(1)
                request_path = match.group(2)
                repo_name = match.group(3)
                user_agent = match.group(4)

                repo_counter[repo_name] += 1

                # Categorize by format using hybrid detection
                format_type = categorize_request(repo_name, user_agent, request_path)
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
