import pypdf

reader = pypdf.PdfReader("/Users/koen/RenGen/CBS_Ref.pdf")
text = ""
for page in reader.pages:
    text += page.extract_text() + "\n"

print(text)
