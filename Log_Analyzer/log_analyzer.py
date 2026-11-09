#!/usr/bin/env python3

#-------------------------------------------------------------------------
# Security Log Analyzer - graphical version.
# © Rui Pinto, 2026 - Version 2.2
#
# Uses only the Python standard library (Tkinter), so there is nothing to
# install. It follows the system light/dark theme automatically.
# Run it with:
#
#    python log_analyzer_gui.py [path/to/file.log]
#-------------------------------------------------------------------------

import csv
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
from collections import Counter, defaultdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import font as tkfont


# --------------------------------------------------
# LOG PARSING (same rules as the command-line version)
# --------------------------------------------------

PATTERNS = {
    "ssh_success": re.compile(
        r"Accepted password for (\S+) from ([\d.]+) port (\d+)"
    ),
    "ssh_failed": re.compile(
        r"Failed password for (?:invalid user )?(\S+) from ([\d.]+) port (\d+)"
    ),
    "http": re.compile(
        r'(?:^|apache2:access:\s*)'
        r'([\d.]+) \S+ \S+ \[([^\]]+)\] '
        r'"(\S+) ([^ ]+) HTTP/[^"]+" (\d{3}) (\d+|-)'
        r'(?: "([^"]*)" "([^"]*)")?'
    ),
    "ids": re.compile(
        r'\[\*\*\] \[(\d+):(\d+):(\d+)\] '
        r'(.+?) \[\*\*\].*?'
        r'([\d.]+):(\d+) -> ([\d.]+):(\d+)'
    ),
    # Fail2Ban in native syslog-wrapped form: Ban, Unban and Found.
    "fail2ban": re.compile(
        r'fail2ban.*?\[\d+\]:\s+\w+\s+'
        r'\[([^\]]+)\]\s+(Ban|Unban|Found)\s+'
        r'(\d{1,3}(?:\.\d{1,3}){3})',
        re.IGNORECASE
    ),
    "ssh_disconnected": re.compile(
        r'sshd\[\d+\]:\s+Disconnected from\s+'
        r'(\d{1,3}(?:\.\d{1,3}){3})\s+port\s+(\d+)',
        re.IGNORECASE
    ),
    "ufw_block": re.compile(
        r'\[UFW BLOCK\].*?\bSRC='
        r'(\d{1,3}(?:\.\d{1,3}){3})'
        r'.*?\bDST=(\d{1,3}(?:\.\d{1,3}){3})',
        re.IGNORECASE
    ),
    "networkmanager": re.compile(
        r'NetworkManager\[\d+\]:\s*<\w+>\s*'
        r'.*?state change:\s*([^\s]+)',
        re.IGNORECASE
    ),
    "apache_notice": re.compile(
        r'apache2:\s*NOTICE:\s*(.+)',
        re.IGNORECASE
    ),
    "audit": re.compile(
        r'kernel:\s*Audit:\s*(.+)',
        re.IGNORECASE
    ),
    "sudo": re.compile(
        r'sudo\[\d+\]:\s+(\S+)\s*:.*?'
        r'USER=(\S+).*?COMMAND=(.+)'
    ),
    "cron": re.compile(
        r'CRON\[\d+\]:\s+\(([^)]+)\)\s+CMD \((.+)\)'
    ),
    "systemd": re.compile(r'systemd\[\d+\]:\s+(.+)'),
}


def analyze_line(line):
    # Identifies and parses a log line.

    m = PATTERNS["ssh_success"].search(line)
    if m:
        username, ip, port = m.groups()
        return {
            "type": "SSH_LOGIN_SUCCESS",
            "ip": ip,
            "detail": f"Login accepted: {username}, port {port}",
        }

    m = PATTERNS["ssh_failed"].search(line)
    if m:
        username, ip, port = m.groups()
        return {
            "type": "SSH_LOGIN_FAILED",
            "ip": ip,
            "detail": f"Failed password: {username}, port {port}",
        }

    m = PATTERNS["http"].search(line)
    if m:
        ip, date, method, path, status, size, _, agent = m.groups()
        status = int(status)

        # Common Log Format lines have no Referer or User-Agent
        detail = f"{method} {path} | HTTP {status} | {size} bytes"

        if agent is not None:
            detail += f" | User-Agent: {agent}"

        return {
            "type": "HTTP",
            "ip": ip,
            "detail": detail,
            "status": status,
            "path": path,
            "agent": agent,
        }

    m = PATTERNS["ids"].search(line)
    if m:
        sid, signature, revision, alert, source_ip, source_port, \
            destination_ip, destination_port = m.groups()

        return {
            "type": "IDS_ALERT",
            "ip": source_ip,
            "detail": (
                f"{alert.strip()} | SID {signature} | "
                f"{source_ip}:{source_port} -> "
                f"{destination_ip}:{destination_port}"
            ),
        }

    m = PATTERNS["ssh_disconnected"].search(line)
    if m:
        ip, port = m.groups()
        return {
            "type": "SSH_DISCONNECTED",
            "ip": ip,
            "detail": f"SSH connection disconnected from {ip}, port {port}",
        }

    m = PATTERNS["ufw_block"].search(line)
    if m:
        source_ip, destination_ip = m.groups()
        return {
            "type": "FIREWALL_BLOCK",
            "ip": source_ip,
            "detail": f"UFW blocked traffic from {source_ip} to {destination_ip}",
        }

    m = PATTERNS["fail2ban"].search(line)
    if m:
        service, action, ip = m.groups()
        action = action.lower()
        if action == "ban":
            event_type = "IP_BANNED"
            detail = f"Fail2ban banned {ip} on service {service}"
        elif action == "unban":
            event_type = "IP_UNBANNED"
            detail = f"Fail2ban unbanned {ip} on service {service}"
        else:
            event_type = "FAIL2BAN_FOUND"
            detail = f"Fail2ban detected {ip} on service {service}"
        return {"type": event_type, "ip": ip, "detail": detail}

    m = PATTERNS["networkmanager"].search(line)
    if m:
        state = m.group(1)
        detail = f"NetworkManager state change: {state}"
        return {
            "type": "NETWORK_EVENT",
            "ip": None,
            "detail": detail,
        }

    m = PATTERNS["apache_notice"].search(line)
    if m:
        return {
            "type": "APACHE_NOTICE",
            "ip": None,
            "detail": m.group(1).strip(),
        }

    m = PATTERNS["audit"].search(line)
    if m:
        return {
            "type": "SECURITY_AUDIT",
            "ip": None,
            "detail": m.group(1).strip(),
        }

    m = PATTERNS["sudo"].search(line)
    if m:
        username, target, command = m.groups()
        return {
            "type": "SUDO",
            "ip": None,
            "detail": f"{username} executed command as {target}: {command}",
        }

    m = PATTERNS["cron"].search(line)
    if m:
        username, command = m.groups()
        return {
            "type": "CRON",
            "ip": None,
            "detail": f"Scheduled task ({username}): {command}",
        }

    m = PATTERNS["systemd"].search(line)
    if m:
        return {
            "type": "SYSTEMD",
            "ip": None,
            "detail": m.group(1),
        }

    return {
        "type": "UNKNOWN",
        "ip": None,
        "detail": line.strip(),
    }


def get_services_from_logs(events):
    # Identifies services and their last known state from log events.

    services = {}

    for event in events:
        if event["type"] != "SYSTEMD":
            continue

        message = event["detail"]

        started = re.search(
            r"Started (.+?)(?:\.|$)",
            message,
            re.IGNORECASE
        )

        stopped = re.search(
            r"Stopped (.+?)(?:\.|$)",
            message,
            re.IGNORECASE
        )

        if started:
            service_name = started.group(1).strip()
            services[service_name] = "ACTIVE"

        elif stopped:
            service_name = stopped.group(1).strip()
            services[service_name] = "STOPPED"

    return services


def identify_log_sources(events):
    # Identifies the log sources found in the analyzed file.
    log_sources = {
        "SSH": {
            "description": "OpenSSH - Remote access and authentication logs",
            "count": 0
        },
        "Apache HTTP": {
            "description": "Apache Web Server - HTTP access logs",
            "count": 0
        },
        "IDS": {
            "description": "Intrusion Detection System - Security alerts",
            "count": 0
        },
        "Fail2Ban": {
            "description": "Fail2Ban - Intrusion prevention and IP banning",
            "count": 0
        },
        "Firewall": {
            "description": "UFW - Firewall blocked traffic",
            "count": 0
        },
        "NetworkManager": {
            "description": "NetworkManager - Network state changes",
            "count": 0
        },
        "Security audit": {
            "description": "Kernel audit and security-related events",
            "count": 0
        },
        "Apache notices": {
            "description": "Apache - Operational and security notices",
            "count": 0
        },
        "SUDO": {
            "description": "Linux SUDO - Privileged command execution",
            "count": 0
        },
        "CRON": {
            "description": "Linux CRON - Scheduled tasks",
            "count": 0
        },
        "SYSTEMD": {
            "description": "Linux SYSTEMD - System and service events",
            "count": 0
        },
        "Unknown": {
            "description": "Unrecognized log entries",
            "count": 0
        }
    }

    for event in events:
        event_type = event["type"]

        if event_type in ("SSH_LOGIN_SUCCESS", "SSH_LOGIN_FAILED"):
            log_sources["SSH"]["count"] += 1

        elif event_type == "HTTP":
            log_sources["Apache HTTP"]["count"] += 1

        elif event_type == "IDS_ALERT":
            log_sources["IDS"]["count"] += 1

        elif event_type in ("IP_BANNED", "IP_UNBANNED", "FAIL2BAN_FOUND"):
            log_sources["Fail2Ban"]["count"] += 1

        elif event_type == "FIREWALL_BLOCK":
            log_sources["Firewall"]["count"] += 1

        elif event_type == "NETWORK_EVENT":
            log_sources["NetworkManager"]["count"] += 1

        elif event_type == "SECURITY_AUDIT":
            log_sources["Security audit"]["count"] += 1

        elif event_type == "APACHE_NOTICE":
            log_sources["Apache notices"]["count"] += 1

        elif event_type == "SUDO":
            log_sources["SUDO"]["count"] += 1

        elif event_type == "CRON":
            log_sources["CRON"]["count"] += 1

        elif event_type == "SYSTEMD":
            log_sources["SYSTEMD"]["count"] += 1

        else:
            log_sources["Unknown"]["count"] += 1

    return {
        name: details
        for name, details in log_sources.items()
        if details["count"] > 0
    }


# --------------------------------------------------
# LOG FORMAT DETECTION
# --------------------------------------------------

# Apache/Nginx access log line: optional "vhost:port" first, then the
# Common Log Format fields. What follows the status and size decides
# the exact format (Common, Combined, extra fields...).
APACHE_ACCESS_RE = re.compile(
    r'(?P<vhost>[^\s"\[\]]+:\d+ )?'
    r'(?P<ip>\S+) \S+ \S+ '
    r'\[\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4}\] '
    r'"[^"]*" \d{3} (?:\d+|-)'
    r'(?P<rest>.*)$'
)

# Referer and User-Agent after the size, plus anything that follows
COMBINED_REST_RE = re.compile(r'^\s+"[^"]*"\s+"[^"]*"(?P<extra>.*)$')

# Other formats, checked in order (most specific first):
# (family, label, description, regex)
OTHER_FORMATS = [
    (
        "Syslog",
        "Lab-prefixed syslog entries",
        "Entries with an explicit auth:, sys:, or fail2ban: source prefix",
        re.compile(r'^(?:auth|sys|fail2ban):\s+', re.IGNORECASE),
    ),
    (
        "Apache",
        "Apache Error Log (2.4)",
        "[date] [module:level] [pid N:tid N] [client ip:port] message",
        re.compile(
            r'^\s*\[\w{3} \w{3} \d{1,2} \d{2}:\d{2}:\d{2}\.\d+ \d{4}\] '
            r'\[[^\]:]+:\w+\] \[pid \d+'
        ),
    ),
    (
        "Apache",
        "Apache Error Log (2.2 style)",
        "[date] [level] [client ip] message",
        re.compile(
            r'^\s*\[\w{3} \w{3} \d{1,2} \d{2}:\d{2}:\d{2} \d{4}\] '
            r'\[\w+\]'
        ),
    ),
    (
        "IDS",
        "Suricata fast.log",
        "MM/DD/YYYY-HH:MM:SS.ffffff  [**] [gid:sid:rev] alert [**] ...",
        re.compile(
            r'^\d{2}/\d{2}/\d{4}-\d{2}:\d{2}:\d{2}\.\d+\s+'
            r'\[\*\*\]\s+\[\d+:\d+:\d+\]'
        ),
    ),
    (
        "IDS",
        "Snort fast alert",
        "MM/DD-HH:MM:SS.ffffff  [**] [gid:sid:rev] alert [**] ...",
        re.compile(
            r'^\d{2}/\d{2}(?:/\d{2})?-\d{2}:\d{2}:\d{2}\.\d+\s+'
            r'\[\*\*\]\s+\[\d+:\d+:\d+\]'
        ),
    ),
    (
        "IDS",
        "IDS fast-style alert",
        "[**] [gid:sid:rev] alert [**] ... (unrecognized timestamp)",
        re.compile(r'\[\*\*\]\s+\[\d+:\d+:\d+\]'),
    ),
    (
        "Fail2Ban",
        "Fail2Ban native log",
        "YYYY-MM-DD HH:MM:SS,mmm fail2ban.component [pid]: LEVEL message",
        re.compile(
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} fail2ban\.'
        ),
    ),
    (
        "Syslog",
        "Syslog RFC 5424",
        "<PRI>VERSION TIMESTAMP HOST APP PROCID MSGID message",
        re.compile(r'^<\d{1,3}>\d{1,2} \S+ \S+ \S+ \S+ \S+'),
    ),
    (
        "Syslog",
        "Syslog RFC 3164 (traditional)",
        "Mon DD HH:MM:SS host process[pid]: message",
        re.compile(
            r'^(?:<\d{1,3}>)?[A-Z][a-z]{2}\s+\d{1,2} '
            r'\d{2}:\d{2}:\d{2} \S+ '
        ),
    ),
    (
        "Syslog",
        "Syslog with ISO 8601 timestamp",
        "YYYY-MM-DDTHH:MM:SS+00:00 host process[pid]: message "
        "(rsyslog high precision / journald short-iso)",
        re.compile(
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
            r'(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})? \S+ '
        ),
    ),
]


def detect_apache_access(line):
    # Identifies which type of Apache (or Nginx) access log a line is.

    # Cheap check to skip most non-HTTP lines quickly
    if '"' not in line or "[" not in line:
        return None

    m = APACHE_ACCESS_RE.search(line)

    if not m:
        return None

    rest = m.group("rest")
    has_vhost = m.group("vhost") is not None

    # Text before the match means the line has a syslog / log-shipper
    # prefix (e.g. "Oct 31 12:00:00 host apache2:access: ...")
    prefixed = m.start() > 0

    combined = COMBINED_REST_RE.match(rest)

    if not rest.strip():
        kind = "common"
    elif combined and not combined.group("extra").strip():
        kind = "combined"
    elif combined:
        kind = "combined_extra"
    else:
        kind = "custom"

    if kind == "custom":
        label = "Apache access log (custom fields)"
        description = (
            "Access log line with extra or non-standard fields after "
            "the status and size"
        )
    else:
        names = {
            "common": "Common Log Format (CLF)",
            "combined": "Combined Log Format",
            "combined_extra": "Combined Log Format + extra fields",
        }

        base_label = names[kind]

        if has_vhost:
            label = "Apache vhost_" + kind.split("_")[0]
            if kind == "combined_extra":
                label += " + extra fields"
        else:
            label = "Apache " + base_label

        if kind == "common":
            description = (
                "Host, ident, user, time, request, status, size "
                "(no Referer or User-Agent)"
            )
        elif kind == "combined":
            description = (
                "Common Log Format + Referer + User-Agent "
                "(Apache default; Nginx 'combined' is identical)"
            )
        else:
            description = (
                "Combined Log Format followed by extra fields "
                "(e.g. response time %D / %T)"
            )

        if has_vhost:
            description = (
                "Virtual-host variant ('%v:%p' first, as in Debian/Ubuntu "
                "other_vhosts_access.log). " + description
            )

    if prefixed:
        label += " (with syslog/shipper prefix)"

    return {
        "family": "Apache",
        "label": label,
        "description": description,
    }


def detect_log_format(line):
    # Identifies the format of a single log line.

    apache = detect_apache_access(line)

    if apache:
        return apache

    for family, label, description, regex in OTHER_FORMATS:
        if regex.search(line):
            return {
                "family": family,
                "label": label,
                "description": description,
            }

    # JSON lines (structured logging)
    stripped = line.strip()

    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            json.loads(stripped)

            return {
                "family": "Structured",
                "label": "JSON lines",
                "description": "One JSON object per line (structured logging)",
            }
        except ValueError:
            pass

    return {
        "family": "Unknown",
        "label": "Unrecognized format",
        "description": "Lines that match none of the known log formats",
    }


# --------------------------------------------------
# ANALYSIS (returns data instead of printing it)
# --------------------------------------------------

SUSPICIOUS_PATHS = ("/admin", "/backup", "/.env", "/wp-admin")


def analyze_log(file_path, threshold, progress_callback=None):
    # Lê o ficheiro de logs e devolve todos os resultados num dicionário.

    event_counts = Counter()
    ssh_failures = Counter()
    ip_counts = Counter()
    suspicious_ips = defaultdict(list)
    events = []

    # Detected log formats: label -> details, count, first line, example
    format_info = {}

    file_size = os.path.getsize(file_path)
    last_reported_bytes = 0

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:

        for line_number, line in enumerate(f, start=1):
            # Actualiza o progresso periodicamente, sem sobrecarregar a fila.
            if progress_callback:
                try:
                    bytes_read = min(f.tell(), file_size)
                except (OSError, ValueError):
                    bytes_read = file_size

                if (
                    bytes_read - last_reported_bytes >= 256 * 1024
                    or bytes_read >= file_size
                ):
                    progress_callback(bytes_read, file_size)
                    last_reported_bytes = bytes_read

            if not line.strip() or line.lstrip().startswith("#"):
                continue

            event = analyze_line(line)
            event["line"] = line_number
            ip = event.get("ip")

            log_format = detect_log_format(line)
            entry = format_info.setdefault(
                log_format["label"],
                {
                    **log_format,
                    "count": 0,
                    "first_line": line_number,
                    "example": line.strip(),
                }
            )
            entry["count"] += 1

            if ip:
                ip_counts[ip] += 1

            events.append(event)
            event_counts[event["type"]] += 1

            occurrence = f"Line {line_number}: {event['detail']}"

            if event["type"] == "SSH_LOGIN_FAILED" and ip:
                ssh_failures[ip] += 1
                suspicious_ips[ip].append(occurrence)

            elif event["type"] in (
                "IDS_ALERT", "IP_BANNED", "FAIL2BAN_FOUND", "FIREWALL_BLOCK"
            ) and ip:
                suspicious_ips[ip].append(occurrence)

            elif event["type"] == "HTTP" and ip:
                if (
                    event["status"] in (401, 403)
                    or event["path"].lower() in SUSPICIOUS_PATHS
                ):
                    suspicious_ips[ip].append(occurrence)

    return {
        "file": str(file_path),
        "threshold": threshold,
        "events": events,
        "event_counts": event_counts,
        "ssh_failures": ssh_failures,
        "ip_counts": ip_counts,
        "suspicious_ips": dict(suspicious_ips),
        "format_info": format_info,
        "log_sources": identify_log_sources(events),
        "services": get_services_from_logs(events),
    }


def sorted_formats(format_info):
    # Formats ordered from the most to the least frequent.

    return sorted(
        format_info.items(),
        key=lambda pair: pair[1]["count"],
        reverse=True
    )


def has_mixed_apache_access(format_info):
    # True when more than one Apache access log format is present.

    labels = [
        label for label, item in format_info.items()
        if item["family"] == "Apache" and "Error Log" not in label
    ]

    return len(labels) > 1


MIXED_APACHE_NOTE = (
    "More than one Apache access log format was found; the file may "
    "mix logs from different servers or virtual hosts."
)


def shorten(text, limit):
    return text if len(text) <= limit else text[:limit - 3] + "..."


def build_text_report(r):
    # Builds the same plain-text report as the command-line version.

    out = []
    add = out.append
    threshold = r["threshold"]

    add("\n" + "=" * 65)
    add("               LOG ANALYSIS REPORT")
    add("=" * 65)
    add(f"Analyzed file: {r['file']}")
    add(f"Total events: {len(r['events'])}")

    add("\n--- LOG SOURCES IDENTIFIED ---")

    if r["log_sources"]:
        for source, details in r["log_sources"].items():
            add(f"\n{source}")
            add(f"  Description: {details['description']}")
            add(f"  Events detected: {details['count']}")

        add(f"\nTotal log sources identified: {len(r['log_sources'])}")
    else:
        add("No recognizable log sources found.")

    add("\n--- LOG FORMATS IDENTIFIED ---")

    if r["format_info"]:
        total_lines = sum(i["count"] for i in r["format_info"].values())

        for label, item in sorted_formats(r["format_info"]):
            percentage = item["count"] / total_lines * 100

            add(f"\n{label}")
            add(f"  Family: {item['family']}")
            add(f"  Description: {item['description']}")
            add(f"  Lines: {item['count']} ({percentage:.1f}%)")
            add(f"  First seen: line {item['first_line']}")
            add(f"  Example: {shorten(item['example'], 90)}")

        add(f"\nTotal distinct formats: {len(r['format_info'])}")

        if has_mixed_apache_access(r["format_info"]):
            add("NOTE: " + MIXED_APACHE_NOTE[0].lower() + MIXED_APACHE_NOTE[1:])
    else:
        add("No log formats found.")

    add("\n--- SERVICES IDENTIFIED IN LOGS ---")

    services = r["services"]

    if services:
        active = sorted(n for n, s in services.items() if s == "ACTIVE")
        stopped = sorted(n for n, s in services.items() if s == "STOPPED")

        add("\nActive services:")
        for name in active:
            add(f"  [ACTIVE] {name}")
        if not active:
            add("  No active services identified.")

        add("\nStopped services:")
        for name in stopped:
            add(f"  [STOPPED] {name}")
        if not stopped:
            add("  No stopped services identified.")

        add(f"\nTotal services identified: {len(services)}")
    else:
        add("No service status information found in the logs.")

    add("\n--- EVENT COUNT BY TYPE ---")

    for event_type, count in r["event_counts"].most_common():
        add(f"{event_type:<22} {count}")

    add("\n--- SSH AUTHENTICATION FAILURES ---")

    if r["ssh_failures"]:
        for ip, count in r["ssh_failures"].most_common():
            level = "ALERT" if count >= threshold else "INFO"
            add(f"[{level}] {ip}: {count} failures")

            if count >= threshold:
                add(f"  Possible brute-force attack (threshold: {threshold})")
    else:
        add("No SSH authentication failures found.")

    add("\n--- POTENTIALLY SUSPICIOUS EVENTS ---")

    if r["suspicious_ips"]:
        for ip, occurrences in sorted(r["suspicious_ips"].items()):
            add(f"\nIP: {ip} ({len(occurrences)} occurrence(s))")

            for occurrence in occurrences:
                add(f"  - {occurrence}")
    else:
        add("No suspicious events found.")

    add("\n--- DETAILED EVENTS ---")

    for event in r["events"]:
        add(f"[Line {event['line']:>3}] {event['type']:<20} {event['detail']}")

    add("\n--- IP ADDRESS COUNTER ---")

    if r["ip_counts"]:
        add(f"{'IP ADDRESS':<20} {'OCCURRENCES':>12}")
        add("-" * 34)

        for ip, count in r["ip_counts"].most_common():
            add(f"{ip:<20} {count:>12}")

        add("-" * 34)
        add(f"{'Unique IPs:':<20} {len(r['ip_counts']):>12}")
        add(
            f"{'Total occurrences:':<20} "
            f"{sum(r['ip_counts'].values()):>12}"
        )
    else:
        add("No IP addresses found in recognized events.")

    add("\nAnalysis completed.")

    return "\n".join(out) + "\n"


# --------------------------------------------------
# GRAPHICAL INTERFACE
# --------------------------------------------------

LIGHT = {
    "BG": "#f3f4f6",
    "CARD": "#ffffff",
    "BORDER": "#d9dde3",
    "TEXT": "#1f2937",
    "MUTED": "#6b7280",
    "ACCENT": "#2f6fed",
    "ACCENT_HOVER": "#2459c9",
    "ACCENT_DISABLED": "#a9bff0",
    "ALERT": "#d64545",
    "OK": "#2e9e5b",
    "WARN": "#b7791f",
    "PURPLE": "#7c5cd6",
    "TEAL": "#1f9d8a",
    "ROW_BAD": "#fde8e8",
    "ROW_GOOD": "#e6f4ea",
    "ROW_WARN": "#fdf3dc",
    "TAB": "#e5e7eb",
    "HEADING": "#e9ecf0",
    "HEADING_HOVER": "#dde1e7",
    "BUTTON": "#e5e7eb",
    "BUTTON_HOVER": "#d5d9e0",
}

DARK = {
    "BG": "#1e2128",
    "CARD": "#2a2e37",
    "BORDER": "#3b414d",
    "TEXT": "#e5e7eb",
    "MUTED": "#9ca3af",
    "ACCENT": "#4c82f7",
    "ACCENT_HOVER": "#6592f8",
    "ACCENT_DISABLED": "#34466f",
    "ALERT": "#f26d6d",
    "OK": "#4cc38a",
    "WARN": "#e0a83a",
    "PURPLE": "#9a7df0",
    "TEAL": "#34c0aa",
    "ROW_BAD": "#4a2a2e",
    "ROW_GOOD": "#23402f",
    "ROW_WARN": "#4a3d1f",
    "TAB": "#252932",
    "HEADING": "#343944",
    "HEADING_HOVER": "#3f4552",
    "BUTTON": "#363b46",
    "BUTTON_HOVER": "#444b58",
}

CURRENT_THEME = "light"
THEME_POLL_MS = 3000  # how often the system theme is checked


def set_palette(name):
    # Loads the light or dark colors into the module-level color names
    # (BG, CARD, TEXT, ...) used by the rest of the interface.
    global CURRENT_THEME

    CURRENT_THEME = "dark" if name == "dark" else "light"
    globals().update(DARK if CURRENT_THEME == "dark" else LIGHT)


set_palette("light")


def _run_quiet(command):
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=1
        )
        return result.stdout.strip().strip("'\"").lower()
    except Exception:
        return ""


def detect_system_theme():
    # Returns "dark" or "light" according to the operating system setting,
    # using only the standard library. Falls back to "light".
    try:
        if sys.platform == "win32":
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion"
                r"\Themes\Personalize"
            ) as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")

            return "light" if value else "dark"

        if sys.platform == "darwin":
            # Prints "Dark" in dark mode; fails (no output) in light mode.
            style = _run_quiet(["defaults", "read", "-g", "AppleInterfaceStyle"])
            return "dark" if "dark" in style else "light"

        # Linux / BSD: GNOME and most GTK-based desktops
        scheme = _run_quiet(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"]
        )
        if "dark" in scheme:
            return "dark"
        if "light" in scheme:
            return "light"

        gtk_theme = _run_quiet(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"]
        ) or os.environ.get("GTK_THEME", "").lower()
        if "dark" in gtk_theme:
            return "dark"

        # KDE Plasma
        for tool in ("kreadconfig6", "kreadconfig5"):
            kde = _run_quiet([tool, "--group", "General", "--key", "ColorScheme"])
            if kde:
                return "dark" if "dark" in kde else "light"
    except Exception:
        pass

    return "light"


def set_title_bar_dark(window, dark):
    # Windows 10/11 only: makes the title bar match the theme.
    if sys.platform != "win32":
        return

    try:
        import ctypes

        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1 if dark else 0)

        for attribute in (20, 19):
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
            )
            if result == 0:
                break
    except Exception:
        pass


MAX_EVENT_ROWS = 10000
MAX_OCCURRENCES_PER_IP = 200
BAD_TYPES = {"SSH_LOGIN_FAILED", "IDS_ALERT", "IP_BANNED", "FAIL2BAN_FOUND", "FIREWALL_BLOCK", "SECURITY_AUDIT", "APACHE_NOTICE"}


class StatCard(tk.Frame):
    # A small box with a big number and a caption.

    def __init__(self, master, caption, fonts):
        super().__init__(master, highlightthickness=1, padx=14, pady=10)

        self.color_name = "TEXT"

        self.value = tk.Label(self, text="-", font=fonts["big"])
        self.value.pack(anchor="w")

        self.caption = tk.Label(self, text=caption, font=fonts["small"])
        self.caption.pack(anchor="w")

        self.apply_theme()

    def apply_theme(self):
        self.config(bg=CARD, highlightbackground=BORDER)
        self.value.config(bg=CARD, fg=globals()[self.color_name])
        self.caption.config(bg=CARD, fg=MUTED)

    def set(self, text, color_name="TEXT"):
        # color_name is the name of a palette color: "TEXT", "OK", ...
        self.color_name = color_name
        self.value.config(text=text, fg=globals()[color_name])


def fit_text(text, font, max_pixels):
    # Trims text with "..." until it fits in max_pixels.

    if font.measure(text) <= max_pixels:
        return text

    while len(text) > 4 and font.measure(text + "...") > max_pixels:
        text = text[:-1]

    return text + "..."


class BarChart(tk.Canvas):
    # Horizontal bar chart drawn on a Canvas (no external libraries).

    def __init__(self, master, title, color_name, fonts):
        super().__init__(
            master,
            bg=CARD,
            height=120,
            highlightthickness=1,
            highlightbackground=BORDER,
        )

        self.title = title
        self.color_name = color_name  # name of a palette color
        self.fonts = fonts
        self.items = []

        self.bind("<Configure>", lambda event: self.redraw())

    def apply_theme(self):
        self.config(bg=CARD, highlightbackground=BORDER)
        self.redraw()

    def set_items(self, items):
        self.items = list(items)
        self.redraw()

    def redraw(self):
        self.delete("all")

        width = self.winfo_width()
        height = self.winfo_height()

        self.create_text(
            12, 16, text=self.title, anchor="w",
            font=self.fonts["bold"], fill=TEXT
        )

        if not self.items:
            self.create_text(
                width / 2, height / 2, text="No data",
                fill=MUTED, font=self.fonts["small"]
            )
            return

        top, bottom = 34, 10
        row_height = min(28, (height - top - bottom) / len(self.items))

        font = self.fonts["small"]
        longest = max(font.measure(label) for label, _ in self.items)
        label_width = max(90, min(int(width * 0.45), longest + 8))

        bar_start = 12 + label_width + 6
        bar_end_max = width - 56
        max_value = max(value for _, value in self.items) or 1

        for index, (label, value) in enumerate(self.items):
            y = top + index * row_height
            middle = y + row_height / 2

            self.create_text(
                12, middle, text=fit_text(label, font, label_width),
                anchor="w",
                font=self.fonts["small"], fill=TEXT
            )

            length = max(2, (bar_end_max - bar_start) * value / max_value)

            self.create_rectangle(
                bar_start, y + 4, bar_start + length, y + row_height - 4,
                fill=globals()[self.color_name], width=0
            )

            self.create_text(
                bar_start + length + 6, middle, text=f"{value:,}",
                anchor="w", font=self.fonts["small"], fill=MUTED
            )


def make_tree(parent, columns, height=8, stretch=None):
    # Creates a Treeview with scrollbars and clickable, sortable headings.
    # columns: list of (id, heading, width, anchor)

    frame = ttk.Frame(parent)
    ids = [column[0] for column in columns]
    stretch = stretch or ids[-1]

    tree = ttk.Treeview(
        frame, columns=ids, show="headings",
        height=height, selectmode="browse"
    )

    for column_id, heading, width, anchor in columns:
        tree.heading(
            column_id, text=heading, anchor=anchor,
            command=lambda c=column_id: sort_tree(tree, c, False)
        )
        tree.column(
            column_id, width=width, minwidth=40,
            anchor=anchor, stretch=(column_id == stretch)
        )

    vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(
        yscrollcommand=vertical.set, xscrollcommand=horizontal.set
    )

    tree.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    style_row_tags(tree)

    return frame, tree


def style_row_tags(tree):
    tree.tag_configure("bad", background=ROW_BAD)
    tree.tag_configure("good", background=ROW_GOOD)
    tree.tag_configure("warn", background=ROW_WARN)


def sort_tree(tree, column, reverse):
    # Sorts a Treeview by a column (numerically when possible).

    rows = [(tree.set(item, column), item) for item in tree.get_children("")]

    def as_number(value):
        return float(value.replace(",", "").replace("%", ""))

    try:
        rows.sort(key=lambda row: as_number(row[0]), reverse=reverse)
    except ValueError:
        rows.sort(key=lambda row: row[0].lower(), reverse=reverse)

    for position, (_, item) in enumerate(rows):
        tree.move(item, "", position)

    tree.heading(
        column, command=lambda: sort_tree(tree, column, not reverse)
    )


def clear_tree(tree):
    tree.delete(*tree.get_children())


class LogAnalyzerApp(ttk.Frame):

    def __init__(self, master):
        super().__init__(master)

        self.result = None
        self.results_queue = queue.Queue()
        self.refresh_job = None
        self.format_examples = {}

        self.path_var = tk.StringVar()
        self.threshold_var = tk.StringVar(value="3")
        self.status_var = tk.StringVar(
            value="Choose a log file and click Analyze."
        )
        self.type_var = tk.StringVar(value="All types")
        self.search_var = tk.StringVar()
        self.example_var = tk.StringVar()

        # Preferência de tema: System, Light ou Dark.
        self.theme_mode_var = tk.StringVar(value="System")
        self.theme_mode = "system"

        base = tkfont.nametofont("TkDefaultFont")
        family = base.actual("family")
        size = abs(base.actual("size")) or 10

        self.fonts = {
            "big": tkfont.Font(family=family, size=size + 10, weight="bold"),
            "bold": tkfont.Font(family=family, size=size, weight="bold"),
            "small": tkfont.Font(family=family, size=size),
        }

        self.build_style()
        self.build_top_bar()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12)

        self.build_overview_tab()
        self.build_sources_tab()
        self.build_services_tab()
        self.build_ssh_tab()
        self.build_events_tab()
        self.build_ips_tab()
        self.build_status_bar()

        self.search_var.trace_add("write", self.schedule_event_refresh)

        # Follow the system light/dark setting while the window is open
        self.theme = CURRENT_THEME
        self.after(THEME_POLL_MS, self.check_theme)

    # ---------- construction ----------

    def build_style(self):
        style = ttk.Style(self)

        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure(
            ".", background=BG, foreground=TEXT,
            bordercolor=BORDER, troughcolor=BG
        )
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("TPanedwindow", background=BG)

        style.configure(
            "TButton", padding=(12, 6), background=BUTTON, foreground=TEXT,
            bordercolor=BORDER, lightcolor=BUTTON, darkcolor=BUTTON
        )
        style.map(
            "TButton",
            background=[("disabled", BG), ("active", BUTTON_HOVER)],
            foreground=[("disabled", MUTED)]
        )

        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab", padding=(14, 6), background=TAB,
            foreground=TEXT, bordercolor=BORDER,
            lightcolor=BORDER, darkcolor=BORDER
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", CARD)],
            foreground=[("selected", TEXT)]
        )

        for name in ("TEntry", "TSpinbox", "TCombobox"):
            style.configure(
                name, fieldbackground=CARD, background=BUTTON,
                foreground=TEXT, insertcolor=TEXT, arrowcolor=TEXT,
                bordercolor=BORDER, lightcolor=CARD, darkcolor=CARD
            )

        style.map(
            "TCombobox",
            fieldbackground=[("readonly", CARD)],
            foreground=[("readonly", TEXT)],
            selectbackground=[("readonly", CARD)],
            selectforeground=[("readonly", TEXT)]
        )

        style.configure(
            "TScrollbar", background=BUTTON, troughcolor=BG,
            bordercolor=BORDER, lightcolor=BUTTON, darkcolor=BUTTON,
            arrowcolor=TEXT
        )
        style.map("TScrollbar", background=[("active", BUTTON_HOVER)])

        style.configure(
            "TProgressbar", troughcolor=BORDER, background=ACCENT,
            bordercolor=BORDER, lightcolor=ACCENT, darkcolor=ACCENT
        )

        style.configure(
            "Treeview", rowheight=24, background=CARD,
            fieldbackground=CARD, foreground=TEXT, bordercolor=BORDER,
            lightcolor=CARD, darkcolor=CARD
        )
        style.configure(
            "Treeview.Heading", background=HEADING, foreground=TEXT,
            font=self.fonts["bold"], relief="flat", padding=(6, 4),
            bordercolor=BORDER, lightcolor=HEADING, darkcolor=HEADING
        )
        style.map(
            "Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "white")]
        )
        style.map("Treeview.Heading", background=[("active", HEADING_HOVER)])

        style.configure(
            "Accent.TButton", background=ACCENT, foreground="white",
            padding=(18, 6), font=self.fonts["bold"],
            bordercolor=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT
        )
        style.map(
            "Accent.TButton",
            background=[
                ("disabled", ACCENT_DISABLED), ("active", ACCENT_HOVER)
            ],
            foreground=[("disabled", "white")]
        )

        # Drop-down list of the combobox (a plain Tk listbox)
        self.option_add("*TCombobox*Listbox.background", CARD)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.option_add("*TCombobox*Listbox.selectForeground", "white")

    def build_top_bar(self):
        bar = ttk.Frame(self, padding=(12, 12, 12, 8))
        bar.pack(fill="x")
        bar.columnconfigure(1, weight=1)

        ttk.Label(bar, text="Log file").grid(row=0, column=0)

        entry = ttk.Entry(bar, textvariable=self.path_var)
        entry.grid(row=0, column=1, sticky="ew", padx=8)
        entry.bind("<Return>", lambda event: self.start_analysis())

        ttk.Button(
            bar, text="Browse...", command=self.browse
        ).grid(row=0, column=2)

        ttk.Label(
            bar, text="SSH failures to alert"
        ).grid(row=0, column=3, padx=(18, 6))

        ttk.Spinbox(
            bar, from_=1, to=9999, width=5,
            textvariable=self.threshold_var
        ).grid(row=0, column=4)

        self.analyze_button = ttk.Button(
            bar, text="Analyze", style="Accent.TButton",
            command=self.start_analysis
        )
        self.analyze_button.grid(row=0, column=5, padx=(18, 6))

        self.export_button = ttk.Button(
            bar, text="Export report...", command=self.export_report,
            state="disabled"
        )
        self.export_button.grid(row=0, column=6)

        ttk.Label(bar, text="Theme").grid(
            row=0, column=7, padx=(18, 6)
        )

        self.theme_combo = ttk.Combobox(
            bar,
            textvariable=self.theme_mode_var,
            state="readonly",
            values=("System", "Light", "Dark"),
            width=9
        )
        self.theme_combo.grid(row=0, column=8)
        self.theme_combo.bind(
            "<<ComboboxSelected>>", self.on_theme_selected
        )

    def build_overview_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab, text="Overview")

        cards = ttk.Frame(tab)
        cards.pack(fill="x")

        self.cards = {}

        for index, (key, caption) in enumerate([
            ("events", "Total events"),
            ("ips", "Unique IPs"),
            ("sources", "Log sources"),
            ("formats", "Log formats"),
            ("alerts", "Brute-force alerts"),
            ("suspicious", "Suspicious IPs"),
        ]):
            card = StatCard(cards, caption, self.fonts)
            card.grid(
                row=0, column=index, sticky="nsew",
                padx=(0 if index == 0 else 8, 0)
            )
            cards.columnconfigure(index, weight=1, uniform="cards")
            self.cards[key] = card

        charts = ttk.Frame(tab)
        charts.pack(fill="both", expand=True, pady=(12, 0))

        for column in (0, 1):
            charts.columnconfigure(column, weight=1, uniform="charts")

        for row in (0, 1):
            charts.rowconfigure(row, weight=1, uniform="chartrows")

        self.chart_types = BarChart(
            charts, "Events by type", "ACCENT", self.fonts
        )
        self.chart_types.grid(
            row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6)
        )

        self.chart_ips = BarChart(
            charts, "Top IP addresses", "PURPLE", self.fonts
        )
        self.chart_ips.grid(
            row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 6)
        )

        self.chart_formats = BarChart(
            charts, "Log formats (lines per format)", "TEAL", self.fonts
        )
        self.chart_formats.grid(
            row=1, column=0, columnspan=2, sticky="nsew", pady=(6, 0)
        )

    def build_sources_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab, text="Sources & Formats")

        ttk.Label(
            tab, text="Log sources identified", font=self.fonts["bold"]
        ).pack(anchor="w")

        frame, self.sources_tree = make_tree(
            tab,
            [
                ("source", "Source", 140, "w"),
                ("description", "Description", 520, "w"),
                ("events", "Events", 90, "e"),
            ],
            height=8,
            stretch="description"
        )
        frame.pack(fill="x", pady=(4, 14))

        ttk.Label(
            tab, text="Log formats identified", font=self.fonts["bold"]
        ).pack(anchor="w")

        frame, self.formats_tree = make_tree(
            tab,
            [
                ("format", "Format", 320, "w"),
                ("family", "Family", 90, "w"),
                ("lines", "Lines", 70, "e"),
                ("share", "Share", 70, "e"),
                ("first", "First seen", 105, "e"),
                ("description", "Description", 520, "w"),
            ],
            height=8
        )
        frame.pack(fill="both", expand=True, pady=(4, 8))

        self.formats_tree.bind("<<TreeviewSelect>>", self.on_format_select)

        self.format_note = ttk.Label(tab, text="", foreground=WARN)
        self.format_note.pack(anchor="w", fill="x")

        self.example_label = ttk.Label(
            tab, textvariable=self.example_var, font="TkFixedFont",
            justify="left"
        )
        self.example_label.pack(anchor="w", fill="x", pady=(4, 0))

        def rewrap(event):
            wrap = max(300, event.width - 30)
            self.format_note.config(wraplength=wrap)
            self.example_label.config(wraplength=wrap)

        tab.bind("<Configure>", rewrap)

    def build_services_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab, text="Services")

        self.services_summary = ttk.Label(
            tab, text="", font=self.fonts["bold"]
        )
        self.services_summary.pack(anchor="w")

        frame, self.services_tree = make_tree(
            tab,
            [
                ("service", "Service", 600, "w"),
                ("state", "Last known state", 160, "w"),
            ],
            height=14,
            stretch="service"
        )
        frame.pack(fill="both", expand=True, pady=(6, 0))

    def build_ssh_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab, text="SSH & Suspicious")

        pane = ttk.PanedWindow(tab, orient="vertical")
        pane.pack(fill="both", expand=True)

        top = ttk.Frame(pane)
        bottom = ttk.Frame(pane)
        pane.add(top, weight=1)
        pane.add(bottom, weight=2)

        self.ssh_label = ttk.Label(
            top, text="SSH authentication failures",
            font=self.fonts["bold"]
        )
        self.ssh_label.pack(anchor="w")

        frame, self.ssh_tree = make_tree(
            top,
            [
                ("ip", "IP address", 180, "w"),
                ("failures", "Failures", 100, "e"),
                ("status", "Status", 400, "w"),
            ],
            height=6
        )
        frame.pack(fill="both", expand=True, pady=(4, 10))

        ttk.Label(
            bottom, text="Potentially suspicious events",
            font=self.fonts["bold"]
        ).pack(anchor="w")

        frame = ttk.Frame(bottom)
        frame.pack(fill="both", expand=True, pady=(4, 0))

        self.suspicious_tree = ttk.Treeview(
            frame, columns=("detail",), show="tree headings",
            selectmode="browse", height=8
        )
        self.suspicious_tree.heading("#0", text="IP address", anchor="w")
        self.suspicious_tree.heading("detail", text="Occurrence", anchor="w")
        self.suspicious_tree.column("#0", width=200, stretch=False)
        self.suspicious_tree.column("detail", width=700, stretch=True)

        vertical = ttk.Scrollbar(
            frame, orient="vertical", command=self.suspicious_tree.yview
        )
        horizontal = ttk.Scrollbar(
            frame, orient="horizontal", command=self.suspicious_tree.xview
        )
        self.suspicious_tree.configure(
            yscrollcommand=vertical.set, xscrollcommand=horizontal.set
        )

        self.suspicious_tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def build_events_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab, text="Events")

        controls = ttk.Frame(tab)
        controls.pack(fill="x", pady=(0, 8))

        ttk.Label(controls, text="Type").pack(side="left")

        self.type_combo = ttk.Combobox(
            controls, textvariable=self.type_var, state="readonly",
            values=["All types"], width=22
        )
        self.type_combo.pack(side="left", padx=(6, 16))
        self.type_combo.bind(
            "<<ComboboxSelected>>", lambda event: self.refresh_events()
        )

        ttk.Label(controls, text="Search").pack(side="left")

        ttk.Entry(
            controls, textvariable=self.search_var, width=34
        ).pack(side="left", padx=(6, 16))

        self.events_count = ttk.Label(controls, text="")
        self.events_count.pack(side="left")

        frame, self.events_tree = make_tree(
            tab,
            [
                ("line", "Line", 70, "e"),
                ("type", "Type", 170, "w"),
                ("ip", "IP address", 140, "w"),
                ("detail", "Detail", 700, "w"),
            ],
            height=16
        )
        frame.pack(fill="both", expand=True)

    def build_ips_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab, text="IP Addresses")

        self.ips_summary = ttk.Label(tab, text="", font=self.fonts["bold"])
        self.ips_summary.pack(anchor="w")

        frame, self.ips_tree = make_tree(
            tab,
            [
                ("ip", "IP address", 200, "w"),
                ("count", "Occurrences", 110, "e"),
                ("share", "Share", 80, "e"),
                ("status", "Status", 300, "w"),
            ],
            height=14
        )
        frame.pack(fill="both", expand=True, pady=(6, 0))

    def build_status_bar(self):
        bar = ttk.Frame(self, padding=(12, 6))
        bar.pack(fill="x")

        self.status_label = ttk.Label(
            bar, textvariable=self.status_var, foreground=MUTED
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        self.view_log_button = ttk.Button(
            bar, text="View log file", command=self.view_log_file
        )
        self.view_log_button.pack(side="right", padx=(10, 0))

        self.progress = ttk.Progressbar(
            bar, mode="indeterminate", length=140
        )
        self.progress.pack(side="right")

    # ---------- theme ----------

    def on_theme_selected(self, event=None):
        # Aplica a preferência escolhida pelo utilizador.
        selected = self.theme_mode_var.get()
        self.theme_mode = selected.lower()

        if self.theme_mode == "system":
            self.apply_theme(detect_system_theme())
        else:
            self.apply_theme(self.theme_mode)

    def check_theme(self):
        # Só acompanha o sistema operativo quando System está seleccionado.
        if self.theme_mode == "system":
            name = detect_system_theme()

            if name != self.theme:
                self.apply_theme(name)

        self.after(THEME_POLL_MS, self.check_theme)

    def apply_theme(self, name):
        self.theme = name
        set_palette(name)

        self.master.configure(bg=BG)
        self.build_style()

        for card in self.cards.values():
            card.apply_theme()

        for chart in (self.chart_types, self.chart_ips, self.chart_formats):
            chart.apply_theme()

        for tree in (
            self.sources_tree, self.formats_tree, self.services_tree,
            self.ssh_tree, self.suspicious_tree, self.events_tree,
            self.ips_tree
        ):
            style_row_tags(tree)

        self.format_note.config(foreground=WARN)
        self.status_label.config(foreground=MUTED)
        self.style_combo_popdown()

        set_title_bar_dark(self.master, name == "dark")

    def style_combo_popdown(self):
        # As listas das drop-downs são criadas na primeira utilização.
        # Recolore-as directamente para acompanhar o tema activo.
        for combo in (self.type_combo, self.theme_combo):
            try:
                popdown = self.tk.eval(
                    f"ttk::combobox::PopdownWindow {combo}"
                )
                self.tk.call(
                    f"{popdown}.f.l", "configure",
                    "-background", CARD, "-foreground", TEXT,
                    "-selectbackground", ACCENT,
                    "-selectforeground", "white"
                )
            except tk.TclError:
                pass

    # ---------- actions ----------

    def browse(self):
        path = filedialog.askopenfilename(
            title="Select a log file",
            filetypes=[
                ("Log files", "*.log *.txt"),
                ("All files", "*.*"),
            ]
        )

        if path:
            self.path_var.set(path)
            self.start_analysis()

    def start_analysis(self):
        text = self.path_var.get().strip().strip('"').strip("'")

        if not text:
            messagebox.showwarning(
                "Log file", "Choose a log file first."
            )
            return

        path = Path(text).expanduser()

        if not path.is_file():
            messagebox.showerror(
                "File not found",
                "File not found. Check the file path and try again."
            )
            return

        try:
            threshold = int(self.threshold_var.get())

            if threshold < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid threshold",
                "The number of SSH failures must be an integer of 1 or more."
            )
            return

        self.set_busy(True)
        self.status_var.set(f"Analyzing {path.name}...")

        worker = threading.Thread(
            target=self.worker, args=(path, threshold), daemon=True
        )
        worker.start()

        self.after(100, self.poll_worker)

    def worker(self, path, threshold):
        # Runs in a background thread so the window stays responsive.

        try:
            started = time.perf_counter()

            def report_progress(bytes_read, total_bytes):
                self.results_queue.put(("progress", bytes_read, total_bytes))

            result = analyze_log(path, threshold, report_progress)
            result["elapsed"] = time.perf_counter() - started

            # Garante que a barra chega aos 100%, mesmo num ficheiro vazio.
            self.results_queue.put(("progress", 1, 1))
            self.results_queue.put(("ok", result))

        except Exception as error:
            self.results_queue.put(("error", str(error)))

    def poll_worker(self):
        finished = False

        while True:
            try:
                message = self.results_queue.get_nowait()
            except queue.Empty:
                break

            kind = message[0]

            if kind == "progress":
                _, bytes_read, total_bytes = message
                percentage = (
                    100 if total_bytes <= 0
                    else min(100, (bytes_read / total_bytes) * 100)
                )
                self.progress.configure(value=percentage)

            elif kind == "ok":
                self.set_busy(False)
                self.show_result(message[1])
                finished = True
                break

            elif kind == "error":
                self.set_busy(False)
                self.progress.configure(value=0)
                self.status_var.set("Analysis failed.")
                messagebox.showerror(
                    "Unable to read the file", message[1]
                )
                finished = True
                break

        if not finished:
            self.after(100, self.poll_worker)

    def set_busy(self, busy):
        if busy:
            self.analyze_button.state(["disabled"])
            self.progress.configure(mode="determinate", maximum=100, value=0)
        else:
            self.analyze_button.state(["!disabled"])
            self.progress.configure(value=100)

    def view_log_file(self):
        # Abre uma janela independente com o conteúdo integral do ficheiro.
        text_path = self.path_var.get().strip().strip('"').strip("'")

        if not text_path:
            messagebox.showwarning(
                "Log file", "Choose a log file first."
            )
            return

        path = Path(text_path).expanduser()

        if not path.is_file():
            messagebox.showerror(
                "Log file not found",
                f"The selected file does not exist:\\n{path}"
            )
            return

        try:
            # utf-8-sig remove, quando existe, a marca BOM do início do ficheiro.
            try:
                content = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                # Permite visualizar também ficheiros com outra codificação.
                content = path.read_text(encoding="utf-8", errors="replace")

        except OSError as error:
            messagebox.showerror(
                "Unable to open log file", str(error)
            )
            return

        viewer = tk.Toplevel(self)
        viewer.title(f"Log file - {path.name}")
        viewer.geometry("1050x700")
        viewer.minsize(650, 400)
        viewer.transient(self.winfo_toplevel())

        heading = ttk.Frame(viewer, padding=(10, 10, 10, 6))
        heading.pack(fill="x")

        ttk.Label(
            heading, text=str(path), font=self.fonts["bold"]
        ).pack(anchor="w")

        line_count = len(content.splitlines())
        ttk.Label(
            heading,
            text=f"{line_count:,} lines  |  {len(content):,} characters"
        ).pack(anchor="w", pady=(3, 0))

        viewer_text = ScrolledText(
            viewer,
            wrap="none",
            font=("Consolas", 10),
            undo=False,
            padx=8,
            pady=8
        )
        viewer_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        viewer_text.insert("1.0", content)
        viewer_text.configure(state="disabled")

        # Reutiliza as cores do tema activo.
        viewer_text.configure(
            background=CARD,
            foreground=TEXT,
            insertbackground=TEXT,
            selectbackground=ACCENT,
            selectforeground="white"
        )

        viewer.bind("<Escape>", lambda event: viewer.destroy())


    def export_report(self):
        # Exports the report in TXT or CSV format.

        if not self.result:
            return

        path = filedialog.asksaveasfilename(
            title="Save report",
            defaultextension=".txt",
            initialfile="report.txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        try:
            # Verify the chosen format by the extension.

            if path.lower().endswith(".json"):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(
                        self.result,
                        f,
                        indent=4,
                        ensure_ascii=False
                    )

                self.status_var.set(f"JSON report saved to {path}")

            elif path.lower().endswith(".csv"):
                # Creates a CSV file compatible with Excel and Calc.
                with open(path, "w", newline="", encoding="utf-8-sig") as f:

                    writer = csv.writer(f, delimiter=";")

                    # Column headers.
                    writer.writerow([
                        "Line",
                        "Event type",
                        "IP address",
                        "Details",
                        "HTTP status",
                        "Path",
                        "User-Agent"
                    ])

                    # Exports all analyzed events.
                    for event in self.result["events"]:
                        writer.writerow([
                            event.get("line", ""),
                            event.get("type", ""),
                            event.get("ip") or "",
                            event.get("detail", ""),
                            event.get("status", ""),
                            event.get("path", ""),
                            event.get("agent") or ""
                        ])

                self.status_var.set(
                    f"CSV report saved to {path}"
                )

            else:
                # Maintains the original .txt export.
                if not path.lower().endswith(".txt"):
                    path += ".txt"

                with open(path, "w", encoding="utf-8") as f:
                    f.write(build_text_report(self.result))

                self.status_var.set(
                    f"Text report saved to {path}"
                )

        except OSError as error:
            messagebox.showerror(
                "Unable to save the report", str(error)
            )

    # ---------- showing results ----------

    def show_result(self, r):
        self.result = r
        threshold = r["threshold"]

        alerts = [
            ip for ip, count in r["ssh_failures"].items()
            if count >= threshold
        ]
        suspicious = r["suspicious_ips"]

        # Summary cards
        self.cards["events"].set(f"{len(r['events']):,}")
        self.cards["ips"].set(f"{len(r['ip_counts']):,}")
        self.cards["sources"].set(str(len(r["log_sources"])))
        self.cards["formats"].set(str(len(r["format_info"])))
        self.cards["alerts"].set(
            str(len(alerts)), "ALERT" if alerts else "OK"
        )
        self.cards["suspicious"].set(
            str(len(suspicious)), "WARN" if suspicious else "OK"
        )

        # Charts
        self.chart_types.set_items(r["event_counts"].most_common(8))
        self.chart_ips.set_items(r["ip_counts"].most_common(8))
        self.chart_formats.set_items(
            [
                (label, item["count"])
                for label, item in sorted_formats(r["format_info"])[:8]
            ]
        )

        self.fill_sources(r)
        self.fill_services(r)
        self.fill_ssh(r, alerts)
        self.fill_suspicious(r)
        self.fill_ips(r, alerts)

        types = sorted(r["event_counts"])
        self.type_combo.config(values=["All types"] + types)
        self.type_var.set("All types")
        self.search_var.set("")
        self.refresh_events()

        self.export_button.state(["!disabled"])
        self.status_var.set(
            f"{r['file']}  -  {len(r['events']):,} events analyzed "
            f"in {r['elapsed']:.2f} s"
        )

    def fill_sources(self, r):
        clear_tree(self.sources_tree)

        for source, details in r["log_sources"].items():
            self.sources_tree.insert(
                "", "end",
                values=(
                    source, details["description"], f"{details['count']:,}"
                )
            )

        clear_tree(self.formats_tree)
        self.format_examples = {}

        total = sum(item["count"] for item in r["format_info"].values())

        for label, item in sorted_formats(r["format_info"]):
            self.formats_tree.insert(
                "", "end", iid=label,
                values=(
                    label,
                    item["family"],
                    f"{item['count']:,}",
                    f"{item['count'] / total * 100:.1f}%",
                    f"line {item['first_line']}",
                    item["description"],
                )
            )
            self.format_examples[label] = item["example"]

        self.format_note.config(
            text=(
                "NOTE: " + MIXED_APACHE_NOTE
                if has_mixed_apache_access(r["format_info"]) else ""
            )
        )

        children = self.formats_tree.get_children()

        if children:
            self.formats_tree.selection_set(children[0])
        else:
            self.example_var.set("")

    def on_format_select(self, event):
        selection = self.formats_tree.selection()

        if selection:
            example = self.format_examples.get(selection[0], "")
            self.example_var.set("Example: " + shorten(example, 300))

    def fill_services(self, r):
        clear_tree(self.services_tree)

        services = r["services"]

        if not services:
            self.services_summary.config(
                text="No service status information found in the logs."
            )
            return

        active = sum(1 for s in services.values() if s == "ACTIVE")

        self.services_summary.config(
            text=(
                f"{len(services)} services identified  -  "
                f"{active} active, {len(services) - active} stopped"
            )
        )

        for name in sorted(services):
            state = services[name]

            self.services_tree.insert(
                "", "end", values=(name, state),
                tags=("good",) if state == "ACTIVE" else ("warn",)
            )

    def fill_ssh(self, r, alerts):
        clear_tree(self.ssh_tree)

        threshold = r["threshold"]

        self.ssh_label.config(
            text=(
                "SSH authentication failures  -  alert at "
                f"{threshold} or more failures from one IP"
            )
        )

        for ip, count in r["ssh_failures"].most_common():
            if count >= threshold:
                status, tags = "ALERT - possible brute-force attack", ("bad",)
            else:
                status, tags = "Info", ()

            self.ssh_tree.insert(
                "", "end", values=(ip, f"{count:,}", status), tags=tags
            )

    def fill_suspicious(self, r):
        tree = self.suspicious_tree
        clear_tree(tree)

        suspicious = r["suspicious_ips"]
        open_groups = len(suspicious) <= 15

        for ip, occurrences in sorted(suspicious.items()):
            parent = tree.insert(
                "", "end", text=ip,
                values=(f"{len(occurrences):,} occurrence(s)",),
                open=open_groups
            )

            for occurrence in occurrences[:MAX_OCCURRENCES_PER_IP]:
                tree.insert(parent, "end", text="", values=(occurrence,))

            hidden = len(occurrences) - MAX_OCCURRENCES_PER_IP

            if hidden > 0:
                tree.insert(
                    parent, "end", text="",
                    values=(
                        f"... and {hidden:,} more "
                        "(export the report to see all)",
                    )
                )

    def fill_ips(self, r, alerts):
        clear_tree(self.ips_tree)

        counts = r["ip_counts"]
        total = sum(counts.values())

        if not counts:
            self.ips_summary.config(
                text="No IP addresses found in recognized events."
            )
            return

        self.ips_summary.config(
            text=(
                f"{len(counts):,} unique IPs  -  "
                f"{total:,} total occurrences"
            )
        )

        for ip, count in counts.most_common():
            if ip in alerts:
                status, tags = "ALERT - SSH brute-force threshold", ("bad",)
            elif ip in r["suspicious_ips"]:
                status, tags = "Suspicious activity", ("warn",)
            else:
                status, tags = "", ()

            self.ips_tree.insert(
                "", "end",
                values=(ip, f"{count:,}", f"{count / total * 100:.1f}%",
                        status),
                tags=tags
            )

    # ---------- events tab ----------

    def schedule_event_refresh(self, *args):
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)

        self.refresh_job = self.after(250, self.refresh_events)

    def refresh_events(self):
        self.refresh_job = None

        clear_tree(self.events_tree)

        if not self.result:
            return

        wanted = self.type_var.get()
        needle = self.search_var.get().strip().lower()

        matched = 0
        shown = 0

        for event in self.result["events"]:
            if wanted != "All types" and event["type"] != wanted:
                continue

            ip = event.get("ip") or ""

            if needle and not (
                needle in event["detail"].lower()
                or needle in event["type"].lower()
                or needle in ip
            ):
                continue

            matched += 1

            if shown >= MAX_EVENT_ROWS:
                continue

            if event["type"] in BAD_TYPES:
                tags = ("bad",)
            elif event["type"] == "SSH_LOGIN_SUCCESS":
                tags = ("good",)
            else:
                tags = ()

            self.events_tree.insert(
                "", "end",
                values=(event["line"], event["type"], ip, event["detail"]),
                tags=tags
            )
            shown += 1

        text = f"{matched:,} matching events"

        if matched > shown:
            text += (
                f"  (showing the first {shown:,}; narrow the filter or "
                "export the report to see all)"
            )

        self.events_count.config(text=text)


def main():
    # Sharper text on high-DPI Windows screens
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    # Pick the light or dark palette from the system setting
    set_palette(detect_system_theme())

    root = tk.Tk()
    root.title("Log Analyzer v2.02b - © Rui Pinto 2026")
    root.geometry("1120x745")
    root.minsize(900, 605)
    root.configure(bg=BG)

    app = LogAnalyzerApp(root)
    app.pack(fill="both", expand=True)
    set_title_bar_dark(root, CURRENT_THEME == "dark")

    # Optional: python log_analyzer_gui.py path/to/file.log
    if len(sys.argv) > 1:
        app.path_var.set(sys.argv[1])
        root.after(200, app.start_analysis)

    root.mainloop()


if __name__ == "__main__":
    main()
