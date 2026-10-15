from falkordb import FalkorDB

db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('acme')


def is_doc_stale(doc_title: str):
    """Check if a document is outdated (a newer ticket changed it)."""
    result = graph.query("""
        MATCH (d:Document {title: $title})<-[:CHANGES]-(t:Ticket)-[:AUTHORED_BY]->(p:Person)
        WHERE t.date > d.last_updated
        RETURN d.title AS doc, d.last_updated AS doc_date,
               t.id AS ticket, t.title AS change, t.date AS change_date,
               p.name AS person
    """, {"title": doc_title})
    return result.result_set


def who_knows_about(topic: str):
    """Find people connected to a topic through tickets or messages."""
    result = graph.query("""
        MATCH (p:Person)<-[:AUTHORED_BY]-(t:Ticket)-[:CHANGES]->(d:Document)
        WHERE d.title CONTAINS $topic OR t.title CONTAINS $topic
        RETURN DISTINCT p.name AS person, p.role AS role, t.id AS ticket
    """, {"topic": topic})
    return result.result_set


def what_changed_about(topic: str):
    """Find recent tickets that changed a document about this topic."""
    result = graph.query("""
        MATCH (t:Ticket)-[:CHANGES]->(d:Document)
        WHERE d.title CONTAINS $topic OR t.title CONTAINS $topic
        RETURN t.id AS ticket, t.title AS change, t.date AS date, d.title AS doc
        ORDER BY t.date DESC
    """, {"topic": topic})
    return result.result_set


def find_process(doc_title: str):
    """Return a document's content by title."""
    result = graph.query("""
        MATCH (d:Document {title: $title})
        RETURN d.title AS title, d.last_updated AS last_updated, d.content AS content
    """, {"title": doc_title})
    return result.result_set


def list_documents():
    """List all documents in the graph."""
    result = graph.query("""
        MATCH (d:Document)
        RETURN d.title AS title, d.last_updated AS last_updated
    """)
    return result.result_set


# The catalogue the LLM sees
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "is_doc_stale",
            "description": "Check if a document is outdated because a newer ticket changed it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_title": {"type": "string", "description": "Exact document title, e.g. 'Deployment Process'"}
                },
                "required": ["doc_title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "who_knows_about",
            "description": "Find people who have worked on a topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic keyword, e.g. 'deploy' or 'payment'"}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "what_changed_about",
            "description": "Find recent tickets that changed something about a topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic keyword"}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_process",
            "description": "Return the content of a document by its title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_title": {"type": "string", "description": "Exact document title"}
                },
                "required": ["doc_title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_documents",
            "description": "List all documents in the company knowledge base.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
]

# Map tool names to Python functions
TOOL_FUNCTIONS = {
    "is_doc_stale": is_doc_stale,
    "who_knows_about": who_knows_about,
    "what_changed_about": what_changed_about,
    "find_process": find_process,
    "list_documents": list_documents,
}