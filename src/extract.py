import re
from datetime import datetime
from falkordb import FalkorDB

# Connect to FalkorDB
db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('acme')

# Clear existing data
graph.query("MATCH (n) DETACH DELETE n")


# --- Helpers ---

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def convert_date(date_str):
    """Convert 'February 15, 2026' to '2026-02-15'."""
    try:
        return datetime.strptime(date_str.strip(), "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return date_str.strip()


# --- Parsers ---

def parse_documents(text):
    documents = []
    blocks = re.split(r'\nDOCUMENT \d+:\s*', '\n' + text)
    for block in blocks[1:]:
        lines = block.strip().split('\n')
        title = lines[0].strip()
        last_updated = ""
        content_lines = []
        for line in lines[1:]:
            if line.startswith("Last Updated:"):
                last_updated = convert_date(line.replace("Last Updated:", "").strip())
            elif line.startswith("---") or line.startswith("==="):
                continue
            elif line.strip() == "":
                continue
            else:
                content_lines.append(line.strip())
        documents.append({
            "title": title,
            "last_updated": last_updated,
            "content": " ".join(content_lines)[:800]
        })
    return documents


def parse_tickets(text):
    tickets = []
    blocks = re.split(r'\nTICKET:\s*', '\n' + text)
    for block in blocks[1:]:
        lines = block.strip().split('\n')
        ticket_id = lines[0].strip()
        title = status = date = author = changes = ""
        content_lines = []
        in_body = False
        for line in lines[1:]:
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
            elif line.startswith("Status:"):
                status = line.replace("Status:", "").strip()
            elif line.startswith("Date Closed:"):
                date = convert_date(line.replace("Date Closed:", "").strip())
            elif line.startswith("Date Opened:"):
                date = convert_date(line.replace("Date Opened:", "").strip())
            elif line.startswith("Author:"):
                author = line.replace("Author:", "").strip()
            elif line.startswith("Changes:"):
                changes = line.replace("Changes:", "").strip()
            elif line.startswith("---"):
                in_body = True
            elif line.startswith("===") or line.strip() == "":
                continue
            elif in_body:
                content_lines.append(line.strip())
        tickets.append({
            "id": ticket_id,
            "title": title,
            "status": status,
            "date": date,
            "author": author,
            "changes": changes,
            "content": " ".join(content_lines)[:500]
        })
    return tickets


def parse_slack(text):
    messages = []
    blocks = re.split(r'\nChannel:\s*', '\n' + text)
    for block in blocks[1:]:
        lines = block.strip().split('\n')
        channel = lines[0].strip()
        date = author = text_content = ""
        in_body = False
        for line in lines[1:]:
            if line.startswith("Date:"):
                date = convert_date(line.replace("Date:", "").strip())
            elif line.startswith("Author:"):
                author = line.replace("Author:", "").strip()
            elif line.startswith("---"):
                in_body = True
            elif line.startswith("===") or line.strip() == "":
                continue
            elif in_body:
                text_content = line.strip()
        messages.append({
            "channel": channel,
            "date": date,
            "author": author,
            "text": text_content
        })
    return messages


def parse_people(text):
    people = []
    blocks = re.split(r'\nName:\s*', '\n' + text)
    for block in blocks[1:]:
        lines = block.strip().split('\n')
        name = lines[0].strip()
        role = team = ""
        for line in lines[1:]:
            if line.startswith("Role:"):
                role = line.replace("Role:", "").strip()
            elif line.startswith("Team:"):
                team = line.replace("Team:", "").strip()
        people.append({"name": name, "role": role, "team": team})
    return people


# --- Read and parse ---

print("Reading data files...")
documents = parse_documents(read_file("data/documents.txt"))
tickets = parse_tickets(read_file("data/tickets.txt"))
messages = parse_slack(read_file("data/slack.txt"))
people = parse_people(read_file("data/people.txt"))

print(f"Parsed {len(people)} people, {len(documents)} documents, "
      f"{len(tickets)} tickets, {len(messages)} messages")


# --- Build the graph ---

# People
for p in people:
    graph.query(
        "CREATE (p:Person {name: $name, role: $role, team: $team})",
        p
    )
print(f"--- Created {len(people)} People ---")

# Documents
for d in documents:
    graph.query(
        "CREATE (d:Document {title: $title, last_updated: $last_updated, content: $content})",
        d
    )
print(f"--- Created {len(documents)} Documents ---")

# Tickets
for t in tickets:
    graph.query(
        "CREATE (t:Ticket {id: $id, title: $title, status: $status, date: $date, content: $content})",
        t
    )
    # Ticket -> Person
    graph.query("""
        MATCH (t:Ticket {id: $id}), (p:Person {name: $author})
        CREATE (t)-[:AUTHORED_BY]->(p)
    """, {"id": t["id"], "author": t["author"]})
    # Ticket -> Document
    if t["changes"]:
        graph.query("""
            MATCH (t:Ticket {id: $id}), (d:Document {title: $doc})
            CREATE (t)-[:CHANGES]->(d)
        """, {"id": t["id"], "doc": t["changes"]})
    print(f"Created Ticket: {t['id']}")

print(f"--- Created {len(tickets)} Tickets ---")

# Messages
for m in messages:
    graph.query(
        "CREATE (m:Message {channel: $channel, date: $date, text: $text})",
        m
    )
    graph.query("""
        MATCH (m:Message {text: $text}), (p:Person {name: $author})
        CREATE (m)-[:POSTED_BY]->(p)
    """, {"text": m["text"], "author": m["author"]})
print(f"--- Created {len(messages)} Messages ---")

print("Graph built successfully from text files!")