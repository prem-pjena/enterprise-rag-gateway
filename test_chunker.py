from services.chunker import split_paragraphs, create_parents, create_children


text = """Refund policy allows refunds within 30 days.

Customers must submit refund requests through the portal.

Shipping fees are non-refundable."""


paragraphs = split_paragraphs(text)

print("PARAGRAPHS:")
for paragraph in paragraphs:
    print("-", paragraph)

print("\nPARENTS:")

parents = create_parents(paragraphs, 100)

for i, parent in enumerate(parents, start=1):
    print(f"\nParent {i} ({len(parent)} characters):")
    print(parent)

print("\nOVERSIZED PARAGRAPH:")

large_paragraph = "A" * 250

parents = create_parents([large_paragraph], 100)

for i, parent in enumerate(parents, start=1):
    print(f"Parent {i} ({len(parent)} characters):")
    print(parent)

print("\nCHILDREN:")

parent = """Refund policy allows refunds within 30 days.

Customers must submit refund requests through the portal.

Shipping fees are non-refundable."""

children = create_children(parent, 60)

for i, child in enumerate(children, start=1):
    print(f"\nChild {i} ({len(child)} characters):")
    print(child)