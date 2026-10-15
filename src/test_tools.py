from tools import is_doc_stale, who_knows_about, what_changed_about, list_documents

print("=== All documents ===")
for row in list_documents():
    print(row)

print("\n=== Is Deployment Process stale? ===")
for row in is_doc_stale("Deployment Process"):
    print(row)

print("\n=== Who knows about deploy? ===")
for row in who_knows_about("Deploy"):
    print(row)

print("\n=== What changed about deploy? ===")
for row in what_changed_about("Deploy"):
    print(row)