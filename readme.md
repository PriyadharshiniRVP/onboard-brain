# Onboarding Brain

An AI agent that answers onboarding questions about a company — and shows you the exact graph query behind every answer.

Built for [Graph Hacks](https://wemakedevs.org) by WeMakeDevs and FalkorDB, October 2026.

**Track:** Company Brain

---

## The Problem

New employees drown in scattered information. The deployment guide is outdated. The process changed in a ticket nobody read. The person who knows the answer is in a Slack thread from six months ago.

Ask a chatbot "How do I deploy to production?" and it gives you a confident answer that might be based on a stale document. You have no way to know. The information is scattered across docs, tickets, Slack messages, and people — and nobody can see the connections.

## The Solution

Onboarding Brain stores a company's knowledge as a graph. Documents, tickets, Slack messages, and people are nodes. The relationships between them — `CHANGES`, `AUTHORED_BY`, `POSTED_BY` — are stored directly.

When you ask a question, the agent:
1. Picks the right tool from a fixed set of pre-written queries
2. Runs the query against FalkorDB
3. Sends the result to the LLM
4. Returns the answer **plus the path it took**

No query generation. No guessing. Every answer comes with a receipt.

---

## Demo

> **You ask:** "How do I deploy to production?"
>
> **The agent answers:** "The Deployment Process document is outdated. ENG-4421 (closed 2026-08-15) updated the pipeline to use Script B, authored by Rahul. Use Script B for all production deployments."
>
> **And shows the path:**
> ```
> → is_doc_stale(doc_title: "Deployment Process")
>     ["Deployment Process", "2026-02-15", "ENG-4421", "Update deploy pipeline to Script B", "2026-08-15", "Rahul"]
>     ["Deployment Process", "2026-02-15", "ENG-4501", "Deploy guide is outdated", "2026-09-25", "Priya"]
> ```

The agent didn't just find the doc. It found the ticket that superseded it, identified the person who made the change, and knew the doc was stale.

---

## Architecture

```
data/*.txt                    ← Raw text files
    ↓
src/extract.py                ← Parses text, builds graph
    ↓
FalkorDB                      ← Graph database (nodes + edges)
    ↓
src/tools.py                  ← 5 fixed Cypher queries
    ↓
src/agent.py                  ← LLM picks tools, writes answer
    ↓
api/main.py                   ← FastAPI endpoint
    ↓
ui/app.py                     ← Streamlit chat interface
```

### The Graph Model

```
(Document) ←[:CHANGES]— (Ticket) —[:AUTHORED_BY]→ (Person)
                                                      ↑
                                  (Message) —[:POSTED_BY]
```

**Nodes:** `Document`, `Ticket`, `Message`, `Person`
**Relationships:** `CHANGES`, `AUTHORED_BY`, `POSTED_BY`

---

## Tech Stack

| Layer | Tool |
|---|---|
| Graph database | FalkorDB (Docker) |
| Query language | Cypher |
| Agent backend | Python + FastAPI |
| LLM | Groq (`openai/gpt-oss-120b`) |
| UI | Streamlit |
| Data source | Synthetic Acme Corp dataset (5 docs, 5 tickets, 5 Slack messages, 4 people) |

---

## How to Run It

### Prerequisites

- Docker Desktop (running)
- Python 3.10+
- A Groq API key ([free at console.groq.com](https://console.groq.com))

### 1. Start FalkorDB

```bash
docker run -p 6379:6379 -p 3000:3000 -it --rm falkordb/falkordb:latest
```

Leave this running. The browser UI is at `http://localhost:3000`.

### 2. Install dependencies

```bash
pip install falkordb fastapi uvicorn openai python-dotenv streamlit requests
```

### 3. Add your API key

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

### 4. Build the graph

```bash
python src/extract.py
```

You should see:
```
Parsed 4 people, 5 documents, 5 tickets, 5 messages
Graph built successfully from text files!
```

### 5. Start the API

```bash
uvicorn api.main:app --reload
```

API runs at `http://127.0.0.1:8000`. Test it at `http://127.0.0.1:8000/docs`.

### 6. Start the UI

```bash
streamlit run ui/app.py
```

Opens at `http://localhost:8501`.

---

## The Five Tools

The agent never writes Cypher. It picks from these five tools:

| Tool | What it does |
|---|---|
| `is_doc_stale` | Has this document been overtaken by a newer ticket? |
| `who_knows_about` | Who should I ping about this topic? |
| `find_process` | Show me the content of this document |
| `list_documents` | What documents exist, and when were they last updated? |
| `what_changed_about` | What's changed recently about this topic? |

Each tool is a hand-written Cypher query in `src/tools.py`. The LLM's job is just to pick the right one and fill in the argument.

---

## Why a Graph?

Because the answer isn't in any one document. It's in the **connection** between a stale doc and the ticket that superseded it, and in the person who authored that ticket.

A vector search would return the doc and both tickets as "similar text" and leave you to figure out which is current. A graph knows the ticket **CHANGES** the doc, because the edge is stored directly.

---

## What I Learned

- Graph databases store relationships as first-class data. That changes what questions you can ask.
- Never let an LLM write the query. Write the queries yourself, let the model pick between them, and validate every argument.
- The path behind an answer is the answer. Show it in the UI, not in a second query.

---

## Project Structure

```
onboarding-brain/
├── data/
│   ├── documents.txt
│   ├── tickets.txt
│   ├── slack.txt
│   └── people.txt
├── src/
│   ├── __init__.py
│   ├── extract.py        # text files → graph
│   ├── tools.py          # 5 Cypher queries
│   └── agent.py          # LLM + tool selection loop
├── api/
│   ├── __init__.py
│   └── main.py           # FastAPI /ask endpoint
├── ui/
│   └── app.py            # Streamlit chat
├── .env                  # GROQ_API_KEY (not committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Author

**Priyadharshini R** — [GitHub](https://github.com/PriyadharshiniRVP)

