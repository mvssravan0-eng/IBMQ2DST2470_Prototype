import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def add_page_borders(section):
    sectPr = section._sectPr
    # check if pgBorders already exists
    for child in sectPr:
        if child.tag.endswith('pgBorders'):
            sectPr.remove(child)
    
    borders_xml = parse_xml(
        f'<w:pgBorders {nsdecls("w")} w:offsetFrom="page">'
        r'<w:top w:val="single" w:sz="12" w:space="24" w:color="000000"/>'
        r'<w:left w:val="single" w:sz="12" w:space="24" w:color="000000"/>'
        r'<w:bottom w:val="single" w:sz="12" w:space="24" w:color="000000"/>'
        r'<w:right w:val="single" w:sz="12" w:space="24" w:color="000000"/>'
        r'</w:pgBorders>'
    )
    sectPr.append(borders_xml)

doc = docx.Document()
add_page_borders(doc.sections[0])
doc.add_paragraph("Hello world with page borders!")
doc.save("test_border.docx")
print("Saved test_border.docx successfully")
