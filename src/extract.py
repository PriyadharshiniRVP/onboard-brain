from falkordb import FalkorDB

# Connect to FalkorDB
db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('acme')

# Clear any existing data (start fresh)
graph.query("MATCH (n) DETACH DELETE n")

# --- Create People ---
people = [
    {"name": "Rahul", "role": "DevOps Engineer", "team": "Platform Team"},
    {"name": "Priya", "role": "Backend Engineer", "team": "Payments Team"},
    {"name": "Arjun", "role": "Technical Writer", "team": "Platform Team"},
    {"name": "Maya", "role": "Engineering Manager", "team": "Platform Team"},
]

for p in people:
    graph.query(
        "CREATE (p:Person {name: $name, role: $role, team: $team})",
        {"name": p["name"], "role": p["role"], "team": p["team"]}
    )
    print(f"Created Person: {p['name']}")

print("--- People done ---")

# --- Create Documents ---
documents = [
    {"title": "Onboarding Guide", "last_updated": "2026-02-15", "content": "Welcome to Acme Corp..."},
    {"title": "Deployment Process", "last_updated": "2026-02-15", "content": "This document describes how Acme Corp deploys services... uses Script A", "says": "Script A"},
    {"title": "Payment System Overview", "last_updated": "2026-07-15", "content": "The Acme Corp payment system handles..."},
    {"title": "Architecture Notes", "last_updated": "2026-09-15", "content": "Acme Corp's platform is organized..."},
    {"title": "Incident Response Plan", "last_updated": "2025-12-15", "content": "This plan defines how Acme Corp responds..."},
]

for d in documents:
    graph.query(
        "CREATE (d:Document {title: $title, last_updated: $last_updated, content: $content})",
        {"title": d["title"], "last_updated": d["last_updated"], "content": d["content"]}
    )
    print(f"Created Document: {d['title']}")

print("--- Documents done ---")

# --- Create Tickets ---
tickets = [
    {"id": "ENG-4421", "title": "Update deploy pipeline to Script B", "status": "Closed", "date": "2026-08-15", "author": "Rahul", "changes": "Deployment Process"},
    {"id": "ENG-4390", "title": "Fix payment gateway timeout", "status": "Closed", "date": "2026-09-15", "author": "Priya", "changes": "Payment System Overview"},
    {"id": "ENG-4455", "title": "Document new architecture", "status": "Closed", "date": "2026-09-24", "author": "Arjun", "changes": "Architecture Notes"},
    {"id": "ENG-4480", "title": "Update incident response contacts", "status": "Closed", "date": "2026-10-08", "author": "Rahul", "changes": "Incident Response Plan"},
    {"id": "ENG-4501", "title": "Deploy guide is outdated", "status": "Open", "date": "2026-09-25", "author": "Priya", "changes": "Deployment Process"},
]

for t in tickets:
    graph.query(
        "CREATE (t:Ticket {id: $id, title: $title, status: $status, date: $date})",
        {"id": t["id"], "title": t["title"], "status": t["status"], "date": t["date"]}
    )
    # Connect ticket to author
    graph.query(
        """
        MATCH (t:Ticket {id: $id}), (p:Person {name: $author})
        CREATE (t)-[:AUTHORED_BY]->(p)
        """,
        {"id": t["id"], "author": t["author"]}
    )
    # Connect ticket to the document it changes
    graph.query(
        """
        MATCH (t:Ticket {id: $id}), (d:Document {title: $doc})
        CREATE (t)-[:CHANGES]->(d)
        """,
        {"id": t["id"], "doc": t["changes"]}
    )
    print(f"Created Ticket: {t['id']}")

print("--- Tickets done ---")

# --- Create Slack Messages ---
messages = [
    {"channel": "#devops", "date": "2026-09-24", "author": "Priya", "text": "Has anyone updated the deploy guide? It still says Script A."},
    {"channel": "#devops", "date": "2026-09-24", "author": "Rahul", "text": "Yeah, we switched to Script B in ENG-4421. I'll update the doc."},
    {"channel": "#general", "date": "2026-08-15", "author": "Arjun", "text": "New onboarding docs are live, check them out."},
    {"channel": "#payments", "date": "2026-09-15", "author": "Priya", "text": "Payment gateway is stable now, the fix is in production."},
    {"channel": "#incidents", "date": "2026-10-08", "author": "Arjun", "text": "If production goes down, ping Rahul or Priya first."},
]

for m in messages:
    graph.query(
        "CREATE (m:Message {channel: $channel, date: $date, text: $text})",
        {"channel": m["channel"], "date": m["date"], "text": m["text"]}
    )
    # Connect message to author
    graph.query(
        """
        MATCH (m:Message {text: $text}), (p:Person {name: $author})
        CREATE (m)-[:POSTED_BY]->(p)
        """,
        {"text": m["text"], "author": m["author"]}
    )
    print(f"Created Message in {m['channel']}")

print("--- Messages done ---")
print("Graph built successfully!")