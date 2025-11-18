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

## How It Works

The script uses multiple ways to accurately identify package formats. That said, this isn't 100% perfect but it should still give you very accurate results:

1. **User-Agent String** (highest confidence) - e.g., "Apache-Maven/3.8.5", "npm/10.2.0"
2. **File Patterns** (medium confidence) - e.g., "maven-metadata.xml", ".pom", ".jar", ".nupkg"
3. **Repository Name** (fallback) - e.g., "maven-central", "npm-proxy", "docker-hub"

The script stops at the first match, ensuring efficient processing while maintaining accuracy.

## Customization

To add or modify format categorization, edit the `get_format_rules()` function:

```python
def get_format_rules():
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
        # Add your own formats here
        'Custom Format': {
            'user_agents': ['custom-client/'],
            'file_patterns': ['.custom'],
            'repo_patterns': ['custom-repo']
        }
    }
```

Each format has three types of detection patterns that are checked in priority order. You only need to add patterns that make sense for your format - empty lists are allowed.

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

- The script parses Nexus request logs and extracts:
  - Repository names from URLs matching `/repository/REPO_NAME/`
  - User-Agent strings for accurate format detection
  - Request paths to identify file types
  - IP addresses for traffic analysis
- **Format Detection**: Works even with custom repository names (like "onacta-snapshots") by analyzing User-Agent and file patterns, not just repository names
- **IP Addresses**: The top 3 clients section helps you identify:
  - Which servers/build agents generate the most traffic
  - Potential candidates for local caching
  - Whether traffic is concentrated (few IPs) or distributed (many IPs)
  - Internal vs external traffic patterns (based on your IP ranges)

