# Nexus Log Analyzer

A simple script to analyze Nexus repository access logs and count requests by package format.

## Rationale

Since version 3.77, sonatype has enforced hard limits for the community edition of the nexus repository, see https://help.sonatype.com/en/usage-center.html#usage-limitations-for-community-edition

This means, that after exceeding those limits, certain operations will cease to work unless you pay for a commercial license.

The idea of this script is to give you an idea which package formats get the most traffic and also which IPs are pulling the most from the nexus repository. 

## Files

- `analyze_nexus_logs.py`

## Usage

```bash
chmod +x analyze_nexus_logs.py
python3 analyze_nexus_logs.py /path/to/nexus-request.log
```

## Output

The script provides:

1. **Repository Breakdown** - Requests per repository (e.g., maven-central, npm-all, docker-hub)
2. **Package Format Summary** - Aggregated by format type (Maven, npm, Docker, NuGet, PyPI, P2/Eclipse)
3. **Percentage Breakdown** - Shows what percentage of traffic each format receives
4. **Top 3 Clients per Format** - Shows the IP addresses generating the most traffic for each package format

## Performance

The script hopefully handles large log files efficiently, we successfully tested with log files >200MB

## Customization

To add or modify format categorization, edit the `categorize_repo()` function:

```python
def categorize_repo(repo_name):
    repo_lower = repo_name.lower()
    
    if 'maven' in repo_lower:
        return 'Maven'
    elif 'npm' in repo_lower:
        return 'npm'
    # Add your own patterns here
    elif 'custom-format' in repo_lower:
        return 'Custom Format'
    # ...
```

## Example Output

```
============================================================
PACKAGE FORMAT SUMMARY
============================================================
  Requests | Percentage | Format
------------------------------------------------------------
   345,234 |     57.24% | Maven
   187,654 |     31.11% | npm
    45,234 |      7.50% | Docker
    15,432 |      2.56% | NuGet
     8,901 |      1.48% | PyPI
       678 |      0.11% | Other
------------------------------------------------------------
   603,133 |    100.00% | TOTAL

============================================================
TOP 3 CLIENTS PER PACKAGE FORMAT
============================================================

Maven:
  Rank |   Requests | IP Address
  ---- | ---------- | ------------------
     1 |    123,456 | 192.168.1.12
     2 |     89,234 | 192.168.1.15
     3 |     45,678 | 192.168.1.20

npm:
  Rank |   Requests | IP Address
  ---- | ---------- | ------------------
     1 |     98,765 | 192.168.1.20
     2 |     54,321 | 192.168.1.25
     3 |     34,568 | 192.168.1.30
```

## Notes

- The script ignores static file requests (like `/static/rapture/`)
- Repository names are extracted from URLs matching `/repository/REPO_NAME/`
- The categorization is based on common Nexus repository naming conventions
- **IP Addresses**: The top 3 clients section helps you identify:
  - Which servers/build agents generate the most traffic
  - Potential candidates for local caching
  - Whether traffic is concentrated (few IPs) or distributed (many IPs)
  - Internal vs external traffic patterns (based on your IP ranges)

