"""
generate_report_docx.py
-----------------------
Generates the comprehensive internship case study report strictly following the 
template format provided by the student, tailored to the Cybersecurity Network 
Threat & Intrusion Profiler project.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_color):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_styled_code_block(doc, code_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "1E1E1E")
    set_cell_margins(cell, top=120, bottom=120, left=200, right=200)
    
    p = cell.paragraphs[0]
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(code_text.strip())
    run.font.name = 'Consolas'
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(220, 220, 220)
    doc.add_paragraph()

def add_page_borders(section):
    sectPr = section._sectPr
    for child in list(sectPr):
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

def build_document():
    doc = docx.Document()
    
    # Page setup
    for sec in doc.sections:
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)
        add_page_borders(sec)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    plots_dir = os.path.join(base_dir, "outputs", "plots")

    # =========================================================================
    # PAGE 1: COVER PAGE
    # =========================================================================
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(36)
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run("Cybersecurity Network Threat & Intrusion Profiler")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(22)
    run.bold = True
    run.font.color.rgb = RGBColor(160, 20, 20)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run("Report submitted as part of the internship program requirement for the degree of")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.italic = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run("BACHELOR OF TECHNOLOGY\nIN\nCOMPUTER SCIENCE ENGINEERING (AI & ML)")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    run.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(24)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run("Submitted by")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.italic = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(15)
    run = p.add_run("V S SRAVAN MALLADI    (A24126552268)")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    run.bold = True

    logo_path = os.path.join(base_dir, "anits_silver_jubilee_logo.png")
    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(8)
        p_logo.paragraph_format.space_after = Pt(12)
        p_logo.add_run().add_picture(logo_path, width=Inches(1.8))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run("DEPARTMENT OF CSE (AI & ML)\n")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    run.bold = True

    run = p.add_run("ANIL NEERUKONDA INSTITUTE OF TECHNOLOGY AND SCIENCES\n")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    run.bold = True

    run = p.add_run("(UGC AUTONOMOUS)\n")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(11)

    run = p.add_run("(Permanently Affiliated to AU, Approved by AICTE, and Accredited by NBA & NAAC with an 'A+' Grade)\n")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(10)
    run.italic = True

    run = p.add_run("SANGIVALASA, Bheemili Mandal, VISAKHAPATNAM – 531162\n")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(11)

    run = p.add_run("2024–2028")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.bold = True

    doc.add_page_break()

    # =========================================================================
    # PAGE 2: BONAFIDE CERTIFICATE
    # =========================================================================
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run("ANIL NEERUKONDA INSTITUTE OF TECHNOLOGY AND SCIENCES\n")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    run.bold = True

    run = p.add_run("(Affiliated to Andhra University)\n")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(11)

    run = p.add_run("SANGIVALASA, VISAKHAPATNAM – 531162\n")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(11)

    run = p.add_run("2024–2028\n")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(11)

    if os.path.exists(logo_path):
        p_logo2 = doc.add_paragraph()
        p_logo2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo2.paragraph_format.space_before = Pt(6)
        p_logo2.paragraph_format.space_after = Pt(10)
        p_logo2.add_run().add_picture(logo_path, width=Inches(1.35))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(16)
    run = p.add_run("BONAFIDE CERTIFICATE")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.bold = True

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(20)
    run = p.add_run("This is to certify that this Internship Report ")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)

    run = p.add_run("“Cybersecurity Network Threat & Intrusion Profiler”")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.bold = True

    run = p.add_run(" under the ")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)

    run = p.add_run("IBM Q2B Pearl Internship Program (IBMQ2D Case Study #18)")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.bold = True

    run = p.add_run(" is the bonafide work of ")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)

    run = p.add_run("V S SRAVAN MALLADI (A24126552268, IBM ID: IBMQ2DST2470)")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.bold = True

    run = p.add_run(" of II/IV CSM carried out Internship under my supervision.")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)

    # Signatures Table (Reviewer & Class Teacher)
    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_table.autofit = False

    cell_rev = sig_table.cell(0, 0)
    cell_ct = sig_table.cell(0, 1)

    p_rev = cell_rev.paragraphs[0]
    p_rev.paragraph_format.line_spacing = 1.15
    p_rev.add_run("REVIEWER\n\n\n").bold = True
    p_rev.add_run("Mrs. Ch Sravanthi Sowdanya\n").bold = True
    p_rev.add_run("Assistant Professor\n")
    p_rev.add_run("Department of CSE(AI & ML)\n")
    p_rev.add_run("ANITS")

    p_ct = cell_ct.paragraphs[0]
    p_ct.paragraph_format.line_spacing = 1.15
    p_ct.add_run("CLASS TEACHER\n\n\n").bold = True
    p_ct.add_run("Mr. P. Santosh Kumar\n").bold = True
    p_ct.add_run("Assistant Professor\n")
    p_ct.add_run("Department of CSE(AI & ML)\n")
    p_ct.add_run("ANITS")

    # HOD section
    p_hod = doc.add_paragraph()
    p_hod.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_hod.paragraph_format.space_before = Pt(20)
    p_hod.paragraph_format.line_spacing = 1.15
    p_hod.add_run("Head Of the Department\n\n\n").bold = True
    p_hod.add_run("DR. K. SELVANI DEEPTHI\n").bold = True
    p_hod.add_run("Department of CSE (AI & ML)\n")
    p_hod.add_run("ANITS.")

    doc.add_page_break()

    # =========================================================================
    # PAGE 3: ACKNOWLEDGEMENT
    # =========================================================================
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(24)
    run = p.add_run("ACKNOWLEDGEMENT")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.bold = True

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(12)
    p.add_run("An endeavor that spans a significant period becomes a success with the advice, encouragement, and support of many well-wishers. I take this opportunity to express my sincere gratitude and appreciation to all those who have been instrumental in making this internship experience both enriching and rewarding.")

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(12)
    p.add_run("First and foremost, I extend my heartfelt thanks to ")
    p.add_run("Dr. K.S. Deepthi").bold = True
    p.add_run(", Head of the Department of Computer Science & Engineering (AI & ML) at ANITS, for her invaluable guidance, support, and encouragement throughout this internship. Her mentorship and insights have been crucial to my growth during this period.")

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(12)
    p.add_run("I would also like to express my deepest appreciation to ")
    p.add_run("IBM and the IBM Q2B Pearl Program coordinators").bold = True
    p.add_run(" for offering me the opportunity to undertake this industry internship program. I am incredibly grateful to the IBM mentors and technical specialists, whose continuous guidance, enterprise expertise, and support have helped me navigate challenges and enhance my machine learning and cybersecurity skills.")

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(12)
    p.add_run("Special gratitude to my reviewer, ")
    p.add_run("Mrs. Ch Sravanthi Sowdanya").bold = True
    p.add_run(", Assistant Professor, and my class teacher, ")
    p.add_run("Mr. P. Santosh Kumar").bold = True
    p.add_run(", Assistant Professor, Department of CSE (AI & ML), for their continuous academic advice, critical reviews, and constant encouragement throughout the development of this prototype.")

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(28)
    p.add_run("My sincere thanks go to all the faculty members of the Computer Science & Engineering (AI & ML) department for their valuable advice. I am equally grateful to the support staff, whose assistance in providing resources whenever required was instrumental in the successful completion of my internship.")

    p_sig = doc.add_paragraph()
    p_sig.paragraph_format.line_spacing = 1.15
    p_sig.paragraph_format.space_before = Pt(20)
    p_sig.add_run("V S SRAVAN MALLADI\n").bold = True
    p_sig.add_run("A24126552268 (IBM ID: IBMQ2DST2470)\n")
    p_sig.add_run("Department of CSE (AI & ML)\n")
    p_sig.add_run("ANITS")

    doc.add_page_break()

    # =========================================================================
    # PAGES 4 & 5: TABLE OF CONTENTS
    # =========================================================================
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(20)
    run = p.add_run("Table of Contents")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(16)
    run.bold = True

    toc_items = [
        ("1. Introduction", "6"),
        ("   1.1 Background of Internship", "6"),
        ("   1.2 Objectives of the Internship", "6"),
        ("   1.3 Importance of AI Technologies in Cybersecurity", "7"),
        ("   1.4 Scope of the Project", "7"),
        ("2. Organization Profile", "8"),
        ("   2.1 Overview of IBM (International Business Machines)", "8"),
        ("   2.2 IBM Q2B Pearl Program & AI Track", "8"),
        ("   2.3 IBM Enterprise Security & Threat Intelligence", "8"),
        ("3. Project Overview", "10"),
        ("   3.1 Title of the Project", "10"),
        ("   3.2 Problem Statement", "10"),
        ("   3.3 Objectives of the Project", "10"),
        ("   3.4 Relevance to Threat Detection and SOC Operations", "10"),
        ("4. Literature Review / Theoretical Background", "11"),
        ("   4.1 Introduction to Network Intrusions and Attack Classes (DoS, Probe, R2L, U2R)", "11"),
        ("   4.2 Role of Artificial Intelligence in Network Threat Detection", "12"),
        ("   4.3 Machine Learning Approaches for Supervised & Unsupervised Detection", "12"),
        ("   4.4 Related Works and Benchmark Datasets", "13"),
        ("5. Methodology", "14"),
        ("   5.1 Data Collection and Dataset Description (NSL-KDD)", "14"),
        ("   5.2 Data Preprocessing (Encoding, Scaling, Zero Leakage)", "15"),
        ("   5.3 Feature Selection and Schema Mapping", "16"),
        ("   5.4 Model Selection – Supervised, Unsupervised & Hybrid Routing", "16"),
        ("   5.5 Model Training and Evaluation Metrics (Macro-F1, ROC-AUC, Zero-Day Recall)", "17"),
        ("6. Implementation", "18"),
        ("   6.1 Week 1 – Data Exploration, Cleaning & Preprocessing", "18"),
        ("   6.2 Week 2 – Model Building, Training & Saving with Joblib", "21"),
        ("   6.3 Week 3 – Deployment of Streamlit Web App", "24"),
        ("   6.4 Improvements Made Over Standard Baselines", "26"),
        ("7. Results and Discussion", "27"),
        ("   7.1 Model Performance (Classification & Anomaly Detection)", "27"),
        ("   7.2 Visualization of Results (Confusion Matrices, ROC Curves, Routing)", "27"),
        ("   7.3 Streamlit App Output (Interface and Flow Profiling)", "29"),
        ("   7.4 Interpretation of Predictions (SHAP Explainability & Case Studies)", "30"),
        ("8. Conclusion & Future Work", "31"),
        ("   8.1 Summary of Learnings", "31"),
        ("   8.2 Technical and Cybersecurity Skills Acquired", "31"),
        ("   8.3 Limitations of the Current Approach", "32"),
        ("   8.4 Future Scope (Live Zeek Ingestion, API Serving, Drift Detection)", "32"),
        ("9. Internship Outcomes", "33"),
        ("   9.1 Technical Skills Acquired", "33"),
        ("   9.2 Soft Skills Developed", "33"),
        ("   9.3 Contribution to Career Growth", "33"),
        ("Appendix", "34"),
        ("   A. Source Code (GitHub Links)", "34"),
        ("   B. Streamlit App Screenshots", "34"),
        ("   C. Certificate of Completion", "36"),
    ]

    toc_table = doc.add_table(rows=len(toc_items), cols=2)
    toc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, (title, page_num) in enumerate(toc_items):
        c0 = toc_table.cell(idx, 0)
        c1 = toc_table.cell(idx, 1)
        c0.paragraphs[0].paragraph_format.line_spacing = 1.15
        c0.paragraphs[0].paragraph_format.space_after = Pt(2)
        c1.paragraphs[0].paragraph_format.line_spacing = 1.15
        c1.paragraphs[0].paragraph_format.space_after = Pt(2)
        c1.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        r0 = c0.paragraphs[0].add_run(title)
        r1 = c1.paragraphs[0].add_run(page_num)
        if not title.startswith("   "):
            r0.bold = True
            r1.bold = True

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 1: INTRODUCTION
    # =========================================================================
    h1 = doc.add_heading("1. Introduction", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(8)

    h2 = doc.add_heading("1.1 Background of Internship", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("This report highlights my learning experience and project deliverables from a four-week virtual internship, completed as part of the academic requirements for the ")
    p.add_run("Bachelor of Technology in Computer Science and Engineering (AI & ML)").bold = True
    p.add_run(" at Anil Neerukonda Institute of Technology and Sciences (ANITS). The internship was offered under the ")
    p.add_run("IBM Q2B Pearl Internship Program (IBMQ2D Case Study #18, UG Level 2)").bold = True
    p.add_run(", focusing on ")
    p.add_run("“Cybersecurity Network Threat & Intrusion Profiler”.").bold = True

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("The IBM Q2B Pearl framework combined structured project-based learning with industry-aligned technical evaluation. Its core mission was to bridge the gap between theoretical classroom concepts in machine learning and enterprise challenges in modern cybersecurity. Through this initiative, IBM provided direct industry problem definitions, architectural expectations, and enterprise threat intelligence frameworks.")

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("As modern enterprise computer networks expand, they face two simultaneous threats: high-volume, automated attacks following established attack signatures (e.g., SYN floods, port scans), and sophisticated, newly invented 'zero-day' exploits that bypass signature-based firewalls. Security Operations Centers (SOCs) struggle with alert fatigue and high false-positive rates from naive anomaly detectors, as well as dangerous blind spots from overconfident supervised models. This project addresses this critical operational challenge by creating a robust, hybrid machine learning profiler.")

    h2 = doc.add_heading("1.2 Objectives of the Internship", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(6)
    p.add_run("The primary objective was to design, implement, evaluate, and deploy an end-to-end intelligent intrusion profiling system combining supervised attack classification with unsupervised zero-day anomaly detection. The specific milestones achieved include:")

    bullets = [
        "To explore and preprocess the standard NSL-KDD network intrusion benchmark without information leakage between training and testing partitions.",
        "To engineer nominal categorical encodings and standard scaling across 41 flow attributes.",
        "To build and compare multi-class supervised classifiers (Decision Tree, Random Forest, XGBoost) capable of categorizing network traffic into 5 standard classes: Normal, DoS, Probe, R2L, and U2R.",
        "To design an unsupervised anomaly detection baseline (Isolation Forest, Local Outlier Factor, Autoencoder/PCA) trained strictly on normal traffic to detect novel, zero-day attacks unseen in training.",
        "To architect a hybrid decision-routing pipeline that automatically mitigates high-confidence known threats while routing uncertain or anomalous traffic to a specialized human-review queue.",
        "To implement a SHAP (SHapley Additive exPlanations) transparency layer to provide interpretable feature attributions for SOC analysts.",
        "To package and deploy the trained models into an interactive, user-friendly Streamlit web dashboard ready for cloud hosting."
    ]
    for b in bullets:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.line_spacing = 1.2
        bp.paragraph_format.space_after = Pt(4)
        bp.add_run(b)

    h2 = doc.add_heading("1.3 Importance of AI Technologies in Cybersecurity", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("Traditional intrusion detection systems (IDS) depend heavily on deterministic, human-written rule signatures (such as Snort rules). While highly reliable for previously observed attack signatures, they completely fail when encountering modified payload patterns, encrypted sessions, or novel zero-day exploits. Artificial Intelligence and Machine Learning transform network defense from reactive signature matching into proactive, behavioral pattern recognition.")

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("Machine learning models can analyze multidimensional telemetry (packet rates, byte volume asymmetries, TCP flags, and host-level error metrics) in microseconds. By modeling normal baseline behaviors, unsupervised algorithms can detect subtle deviations indicating zero-day lateral movement or privilege escalation that human analysts would miss amid millions of background packets.")

    h2 = doc.add_heading("1.4 Scope of the Project", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("The scope of this project encompasses data cleaning, categorical one-hot encoding, feature normalization, training supervised tree-ensemble classifiers, evaluating unsupervised density and isolation anomaly detectors on a true zero-day test partition (17 unseen attack types), constructing a hybrid routing engine, conducting exact SHAP explainability analyses, and deploying the complete system into an accessible Streamlit web application.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 2: ORGANIZATION PROFILE
    # =========================================================================
    h1 = doc.add_heading("2. Organization Profile", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(8)

    h2 = doc.add_heading("2.1 Overview of IBM (International Business Machines Corporation)", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("International Business Machines Corporation (IBM) is a global leader in hybrid cloud technology, enterprise artificial intelligence, and enterprise-grade cybersecurity solutions. With a rich history spanning over a century, IBM operates in more than 175 countries, driving innovations across data science, quantum computing, and information security. Enterprise solutions like IBM QRadar SIEM, Cloud Pak for Security, and Guardium are benchmarks in security operations centers worldwide.")

    h2 = doc.add_heading("2.2 IBM Q2B Pearl Program & Artificial Intelligence Initiative", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("The IBM Q2B Pearl initiative is an intensive, project-driven technical program designed to cultivate engineering excellence in foundational and advanced AI disciplines. Under this program, undergraduate students are tasked with solving authentic industrial case studies, mastering applied machine learning architectures, data hygiene standards, and model explainability to prepare them for enterprise AI deployment.")

    h2 = doc.add_heading("2.3 IBM Enterprise Security & Threat Intelligence Alignment", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("In modern Security Operations Centers (SOCs), triaging vast volumes of telemetry requires tight alignment between automated threat classification and human escalation paths. This project directly mirrors the detection paradigms used in IBM security systems: automating known malicious signature handling while applying anomaly profiling to flag zero-day vectors for Tier-2 analyst intervention.")

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.add_run("Logistical and Operational Details of the IBM Q2B Pearl Internship:").bold = True

    org_table_data = [
        ("Aspect", "Details"),
        ("Program Name", "IBM Q2B Pearl Internship Program (AI & Machine Learning Track)"),
        ("Sponsoring Organization", "IBM (International Business Machines Corporation)"),
        ("Student Name", "V S Sravan Malladi"),
        ("Roll Number", "A24126552268"),
        ("IBM Student ID", "IBMQ2DST2470"),
        ("Department & College", "Department of CSE (AI & ML), ANITS (Autonomous), Visakhapatnam"),
        ("Project Case Study", "IBMQ2D Case Study #18: Cybersecurity Network Threat & Intrusion Profiler"),
        ("Level & Module", "UG Level 2 — Module 6: Artificial Intelligence and Machine Learning"),
        ("Core Stack", "Python 3.12, scikit-learn, XGBoost, SHAP, Joblib, Streamlit"),
        ("Primary Deliverables", "Modular Python Pipeline, Serialized Joblib Models, Web App, Technical Report")
    ]
    tbl_org = doc.add_table(rows=len(org_table_data), cols=2)
    tbl_org.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, (k, v) in enumerate(org_table_data):
        c0 = tbl_org.cell(idx, 0)
        c1 = tbl_org.cell(idx, 1)
        set_cell_margins(c0, top=60, bottom=60, left=100, right=100)
        set_cell_margins(c1, top=60, bottom=60, left=100, right=100)
        c0.paragraphs[0].add_run(k)
        c1.paragraphs[0].add_run(v)
        if idx == 0:
            set_cell_background(c0, "E2E8F0")
            set_cell_background(c1, "E2E8F0")
            c0.paragraphs[0].runs[0].bold = True
            c1.paragraphs[0].runs[0].bold = True
        else:
            c0.paragraphs[0].runs[0].bold = True

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 3: PROJECT OVERVIEW
    # =========================================================================
    h1 = doc.add_heading("3. Project Overview", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(8)

    h2 = doc.add_heading("3.1 Title of the Project", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("Cybersecurity Network Threat & Intrusion Profiler using Hybrid Machine Learning and Streamlit Deployment\n(Artificial Intelligence Applied to Threat Intelligence & Security Operations)")

    h2 = doc.add_heading("3.2 Problem Statement", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("Security Operations Centers face three critical compounding bottlenecks when relying on standalone machine learning systems:")

    probs = [
        "Supervised Blind Spots: Purely supervised models trained on historical data are blind to unseen attack families. When evaluated on novel zero-day attacks, they do not flag them as uncertain; instead, they misclassify them as benign 'Normal' traffic with high statistical confidence (>99%).",
        "Alert Fatigue from Naive Anomaly Detection: Standalone anomaly detectors lack attack taxonomy context and flag normal traffic variations as anomalous, overwhelming SOC analysts with high false alarm rates.",
        "Lack of Decision Routing: Most systems enforce binary classification or force packets into known labels, failing to separate 'confidently blocked known attacks' from 'novel behaviors requiring human investigation'."
    ]
    for pb in probs:
        p_item = doc.add_paragraph(style='List Bullet')
        p_item.paragraph_format.line_spacing = 1.2
        p_item.paragraph_format.space_after = Pt(4)
        p_item.add_run(pb)

    h2 = doc.add_heading("3.3 Objectives of the Project", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("1. Construct a clean, leakage-free multi-class classifier using gradient boosted decision trees (XGBoost) to identify known attack classes.\n2. Build an unsupervised anomaly detector (Isolation Forest) trained strictly on normal traffic to capture genuine zero-day attacks.\n3. Implement an intelligent hybrid decision router with an explicit confidence threshold (0.60) and 95th percentile anomaly gate.\n4. Explain decisions using exact SHAP TreeExplainer attributions.\n5. Package the system as an interactive Streamlit application with preset traffic simulations.")

    h2 = doc.add_heading("3.4 Relevance to Threat Detection and SOC Operations", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("This prototype directly aligns with modern Tier-1/Tier-2 SOC triage workflows. High-confidence known attacks (e.g. Neptune DoS at 99.9% confidence) are auto-mitigated without manual intervention, while novel or low-confidence traffic is automatically routed to a dedicated Zero-Day review queue with attached SHAP explanations, saving valuable analyst time and eliminating dangerous blind spots.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 4: LITERATURE REVIEW
    # =========================================================================
    h1 = doc.add_heading("4. Literature Review / Theoretical Background", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(8)

    h2 = doc.add_heading("4.1 Introduction to Network Intrusions and Attack Classes", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("In network security, intrusions are categorized into four standardized tactical attack classes:")

    attack_classes = [
        ("Denial of Service (DoS):", " Flooding network bandwidth or server connection tables to exhaust compute resources and deny access to legitimate users (e.g., Neptune, Smurf, Pod, Teardrop)."),
        ("Surveillance / Probing (Probe):", " Scanning network ports and host IP ranges to identify active operating systems, open services, and vulnerable configurations prior to exploitation (e.g., Satan, Ipsweep, Nmap, Portsweep)."),
        ("Remote to Local (R2L):", " An unauthorized remote attacker attempting to gain local user privileges on a private target machine (e.g., Guess Password, Warezclient, Ftp_write, Snmpguess)."),
        ("User to Root (U2R):", " An attacker starting with basic local user credentials who exploits system buffer overflows or software vulnerabilities to gain root/administrator privileges (e.g., Buffer_overflow, Loadmodule, Rootkit).")
    ]
    for title, desc in attack_classes:
        p_ac = doc.add_paragraph(style='List Bullet')
        p_ac.paragraph_format.line_spacing = 1.2
        p_ac.paragraph_format.space_after = Pt(4)
        p_ac.add_run(title).bold = True
        p_ac.add_run(desc)

    h2 = doc.add_heading("4.2 Role of Artificial Intelligence in Network Threat Detection", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("AI algorithms replace brittle heuristic signatures with probabilistic decision boundaries. Gradient boosted trees learn non-linear interactions across rate and error variables (such as srv_serror_rate and dst_host_same_srv_rate), enabling detection of distributed probing and stealthy brute-force logins that pass traditional firewall threshold filters.")

    h2 = doc.add_heading("4.3 Machine Learning Approaches for Supervised & Unsupervised Detection", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("Supervised learning operates under closed-world assumptions: it requires exhaustive labeled examples of all target classes. When presented with unseen attack families, supervised models fail to generalize. Conversely, unsupervised anomaly detection models (Isolation Forests, Autoencoders) learn open-world density boundaries of normal traffic. By isolating anomalous instances via recursive random splitting, Isolation Forest measures how few splits are required to isolate a flow—making it exceptionally suited for high-dimensional tabular network flows.")

    h2 = doc.add_heading("4.4 Related Works and Benchmark Datasets", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("While the original KDD Cup 1999 dataset was widely cited, research by Tavallaee et al. (2009) proved that it suffered from massive record duplication (over 78% redundant records in train, 75% in test), which caused machine learning models to overfit and report artificially inflated accuracy (>98%). The NSL-KDD dataset solved this by eliminating duplicates and constructing an intentionally harder test partition (KDDTest+) containing 17 novel attack types absent in training, making it the premier benchmark for evaluating true zero-day detection.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 5: METHODOLOGY
    # =========================================================================
    h1 = doc.add_heading("5. Methodology", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(8)

    h2 = doc.add_heading("5.1 Data Collection and Dataset Description (NSL-KDD)", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("The study utilizes the official NSL-KDD dataset comprising two key partitions:\n• KDDTrain+.txt: 125,973 connection records used exclusively for preprocessing and model training.\n• KDDTest+.txt: 22,544 connection records used strictly for out-of-sample evaluation.\n\nCrucially, KDDTest+ contains 3,750 connection records belonging to 17 attack types that NEVER appear in KDDTrain+ (apache2, httptunnel, mailbomb, mscan, named, processtable, ps, saint, sendmail, snmpgetattack, snmpguess, sqlattack, udpstorm, worm, xlock, xsnoop, xterm). This subset forms our true zero-day benchmark.")

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    p.add_run("Class Distribution across NSL-KDD Partitions:").bold = True

    dist_data = [
        ("Traffic Category", "Training Set (KDDTrain+)", "Test Set (KDDTest+)", "Proportion in Train"),
        ("Normal", "67,343", "9,711", "53.46%"),
        ("DoS", "45,927", "7,460", "36.46%"),
        ("Probe", "11,656", "2,421", "9.25%"),
        ("R2L", "995", "2,885", "0.79%"),
        ("U2R", "52", "67", "0.04%"),
        ("Total Records", "125,973", "22,544", "100.0%")
    ]
    tbl_dist = doc.add_table(rows=len(dist_data), cols=4)
    tbl_dist.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, row in enumerate(dist_data):
        for c_idx, val in enumerate(row):
            cell = tbl_dist.cell(idx, c_idx)
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            cell.paragraphs[0].add_run(val)
            if idx == 0:
                set_cell_background(cell, "E2E8F0")
                cell.paragraphs[0].runs[0].bold = True
            elif idx == len(dist_data)-1:
                cell.paragraphs[0].runs[0].bold = True

    h2 = doc.add_heading("5.2 Data Preprocessing (Encoding, Scaling, Zero Leakage)", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.add_run("1. Nominal Categorical Encoding: The three nominal features (protocol_type, service, flag) were encoded using OneHotEncoder(handle_unknown='ignore'). Label encoding was strictly avoided because nominal categories possess no intrinsic ordering; applying arbitrary integer labels introduces fictitious distances that distort distance-based and linear estimators. Setting handle_unknown='ignore' ensures unseen test services get an all-zero encoding without crashing.\n2. Feature Standardization: 38 continuous numeric attributes were scaled using StandardScaler fit exclusively on KDDTrain+.\n3. Class Imbalance Mitigation: Instead of synthetic interpolation (SMOTE)—which fabricates unrealistic network packets in a 122-dimensional sparse space—we utilized cost-sensitive balanced sample weighting.")

    h2 = doc.add_heading("5.3 Feature Selection and Schema Mapping", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("The 41 input features capture three fundamental tiers of flow telemetry: Basic connection features (duration, protocol_type, service, flag, src_bytes, dst_bytes), Content features (logged_in, num_failed_logins, root_shell, is_guest_login), and Traffic rate features (count, srv_count, same_srv_rate, dst_host_srv_count). All fine-grained attack types are mapped down to the 5 standard categories: Normal, DoS, Probe, R2L, and U2R.")

    h2 = doc.add_heading("5.4 Model Selection – Supervised, Unsupervised & Hybrid Routing", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("• Part 1 (Supervised): XGBoost classifier (gradient boosted trees) trained on KDDTrain+ with balanced sample weights.\n• Part 2 (Unsupervised): Isolation Forest (300 estimators) trained strictly on normal traffic.\n• Part 3 (Hybrid Engine): Routes connections based on classifier confidence (>= 0.60) and anomaly score. If the classifier is confident and corroborated, the known label is auto-blocked. If unconfident or anomalous, the connection is routed to 'Unknown / Zero-Day Suspect'.")

    h2 = doc.add_heading("5.5 Model Training and Evaluation Metrics", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("Accuracy alone is misleading on imbalanced datasets. We evaluate: Macro-F1 (equal weighting across all classes), Per-Class Recall (confusion matrix), ROC-AUC / Average Precision (threshold-independent anomaly quality), and True Zero-Day Recall (detection rate specifically across the 17 unseen attack types).")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 6: IMPLEMENTATION
    # =========================================================================
    h1 = doc.add_heading("6. Implementation", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(8)

    h2 = doc.add_heading("6.1 Week 1 – Data Exploration, Cleaning & Preprocessing", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(6)
    p.add_run("During Week 1, the data schema was mapped, column headers assigned, and an automated detector for 42 vs 43 column distributions implemented. The preprocessing pipeline was constructed using scikit-learn ColumnTransformer:")

    code_w1 = """import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

CATEGORICAL_COLS = ["protocol_type", "service", "flag"]

def build_preprocessor(numeric_cols):
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_COLS),
        ],
        remainder="drop",
    )

def fit_transform_train_test(train_df, test_df):
    feature_cols = [c for c in train_df.columns if c not in {"label", "category", "binary_label", "difficulty"}]
    numeric_cols = [c for c in feature_cols if c not in CATEGORICAL_COLS]
    
    preprocessor = build_preprocessor(numeric_cols)
    X_train = preprocessor.fit_transform(train_df[feature_cols])
    X_test = preprocessor.transform(test_df[feature_cols])
    return X_train, X_test, preprocessor"""
    add_styled_code_block(doc, code_w1)

    h2 = doc.add_heading("6.2 Week 2 – Model Building, Training & Saving with Joblib", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(6)
    p.add_run("During Week 2, both the multiclass XGBoost classifier and the normal-only Isolation Forest anomaly detector were trained. Models, label encoders, preprocessor transformers, and metadata thresholds were serialized using Joblib:")

    code_w2 = """import joblib
from xgboost import XGBClassifier
from sklearn.ensemble import IsolationForest
from sklearn.utils.class_weight import compute_sample_weight

# 1. Train Multiclass XGBoost
xgb_clf = XGBClassifier(n_estimators=300, max_depth=8, learning_rate=0.1,
                        eval_metric="mlogloss", random_state=42, tree_method="hist")
sw = compute_sample_weight(class_weight="balanced", y=y_train_multi)
xgb_clf.fit(X_train, y_train_multi, sample_weight=sw)

# 2. Train Isolation Forest (Normal-only)
normal_mask = (train_df["binary_label"] == 0).values
iso = IsolationForest(n_estimators=300, contamination=0.1, random_state=42, n_jobs=-1)
iso.fit(X_train[normal_mask])

# 3. Serialize artifacts
joblib.dump(preprocessor, 'models/preprocessor.joblib')
joblib.dump(xgb_clf, 'models/xgb_classifier.joblib')
joblib.dump(iso, 'models/isolation_forest.joblib')"""
    add_styled_code_block(doc, code_w2)

    h2 = doc.add_heading("6.3 Week 3 – Deployment of Streamlit Web App", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(6)
    p.add_run("In Week 3, the interactive Streamlit application (app.py) was built. It loads the cached Joblib artifacts and allows SOC analysts to test traffic presets, inspect decision gates, view probability distributions, and examine explainability plots:")

    code_w3 = """import streamlit as st
import joblib, numpy as np, pandas as pd

@st.cache_resource
def load_models():
    preproc = joblib.load('models/preprocessor.joblib')
    clf = joblib.load('models/xgb_classifier.joblib')
    iso = joblib.load('models/isolation_forest.joblib')
    return preproc, clf, iso

preprocessor, xgb_clf, iso_forest = load_models()

# Hybrid Decision Logic
probs = xgb_clf.predict_proba(X_encoded)[0]
pred_class = label_encoder.inverse_transform([np.argmax(probs)])[0]
conf = np.max(probs)
anom_score = -iso_forest.score_samples(X_encoded)[0]

if pred_class == "Normal" and anom_score < anom_thresh:
    st.success("Result: Normal Traffic (Routine Telemetry)")
elif conf >= 0.60 and anom_score >= anom_thresh:
    st.error(f"Result: Confirmed Attack ({pred_class}) - Auto-Mitigated")
else:
    st.warning("Result: Unknown / Zero-Day Suspect - Escalated to SOC Analyst")"""
    add_styled_code_block(doc, code_w3)

    h2 = doc.add_heading("6.4 Improvements Made Over Standard Baselines", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("1. Zero Data Leakage: Standard tutorials fit scalers on combined train+test sets, causing artificial test-set contamination. Our pipeline strictly fits on KDDTrain+ only.\n2. Preserved Realistic Flow Physics: We avoided SMOTE data synthesis in favor of balanced sample weighting, preventing fictitious flows in sparse spaces.\n3. Calibrated Hybrid Escalation: Replaced arbitrary guessing with an explicit 0.60 confidence gate and 95th percentile anomaly boundary.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 7: RESULTS AND DISCUSSION
    # =========================================================================
    h1 = doc.add_heading("7. Results and Discussion", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(8)

    h2 = doc.add_heading("7.1 Model Performance (Classification & Anomaly Detection)", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(6)
    p.add_run("Supervised Classification Results on KDDTest+ (22,544 rows):").bold = True

    cls_perf_data = [
        ("Task", "Model", "Accuracy", "Macro Precision", "Macro Recall", "Macro F1"),
        ("Binary", "Decision Tree", "0.778", "0.815", "0.801", "0.777"),
        ("Binary", "Random Forest", "0.779", "0.817", "0.802", "0.778"),
        ("Binary", "XGBoost (Best)", "0.797", "0.828", "0.818", "0.797"),
        ("Multiclass", "Decision Tree", "0.748", "0.583", "0.503", "0.490"),
        ("Multiclass", "Random Forest", "0.739", "0.765", "0.475", "0.479"),
        ("Multiclass", "XGBoost (Best)", "0.779", "0.825", "0.557", "0.581")
    ]
    tbl_cls = doc.add_table(rows=len(cls_perf_data), cols=6)
    tbl_cls.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, row in enumerate(cls_perf_data):
        for c_idx, val in enumerate(row):
            cell = tbl_cls.cell(idx, c_idx)
            set_cell_margins(cell, top=50, bottom=50, left=60, right=60)
            cell.paragraphs[0].add_run(val)
            if idx == 0:
                set_cell_background(cell, "E2E8F0")
                cell.paragraphs[0].runs[0].bold = True
            elif "XGBoost" in row[1]:
                cell.paragraphs[0].runs[0].bold = True

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.add_run("Unsupervised Anomaly Detection on True Zero-Day Attacks (3,750 unseen samples):").bold = True

    anom_perf_data = [
        ("Model", "ROC-AUC", "Avg. Precision", "Catch Rate (All Attacks)", "Catch Rate (True Zero-Day)"),
        ("Isolation Forest (Best)", "0.942", "0.954", "67.3%", "63.1%"),
        ("Local Outlier Factor", "0.881", "0.857", "22.5%", "17.4%"),
        ("PCA Reconstruction", "0.935", "0.929", "54.6%", "39.0%")
    ]
    tbl_anom = doc.add_table(rows=len(anom_perf_data), cols=5)
    tbl_anom.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, row in enumerate(anom_perf_data):
        for c_idx, val in enumerate(row):
            cell = tbl_anom.cell(idx, c_idx)
            set_cell_margins(cell, top=50, bottom=50, left=60, right=60)
            cell.paragraphs[0].add_run(val)
            if idx == 0:
                set_cell_background(cell, "E2E8F0")
                cell.paragraphs[0].runs[0].bold = True
            elif idx == 1:
                cell.paragraphs[0].runs[0].bold = True

    h2 = doc.add_heading("7.2 Visualization of Results", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("The figures below illustrate the comparative performance, multi-class confusion matrix, and ROC/PR separation:")

    fig1_path = os.path.join(plots_dir, "model_comparison_classification.png")
    if os.path.exists(fig1_path):
        doc.add_paragraph()
        doc.add_picture(fig1_path, width=Inches(5.5))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.add_run("Figure 1: Classification model comparison across accuracy, macro-F1, and weighted-F1.").italic = True

    fig2_path = os.path.join(plots_dir, "confmat_multiclass_XGBoost.png")
    if os.path.exists(fig2_path):
        doc.add_paragraph()
        doc.add_picture(fig2_path, width=Inches(5.5))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.add_run("Figure 2: Multiclass XGBoost Confusion Matrix (raw counts and row-normalized recall).").italic = True

    fig3_path = os.path.join(plots_dir, "anomaly_roc_pr.png")
    if os.path.exists(fig3_path):
        doc.add_paragraph()
        doc.add_picture(fig3_path, width=Inches(5.5))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.add_run("Figure 3: ROC curve (AUC=0.942) and PR curve for unsupervised anomaly detectors.").italic = True

    h2 = doc.add_heading("7.3 Streamlit App Output (Screenshots and Explanation)", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("The deployed web application provides an interactive cybersecurity command dashboard. SOC analysts can select connection presets (Normal HTTP, Neptune DoS, Port Scan Probe, Password Guess R2L, Buffer Overflow U2R, or True Zero-Day SNMP Attack), adjust connection parameters, and obtain immediate hybrid triage decisions with confidence meters and anomaly scores.")

    fig4_path = os.path.join(plots_dir, "hybrid_routing_breakdown.png")
    if os.path.exists(fig4_path):
        doc.add_paragraph()
        doc.add_picture(fig4_path, width=Inches(5.0))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.add_run("Figure 4: Hybrid pipeline routing breakdown by traffic type (Normal, Known Attack, Zero-Day).").italic = True

    h2 = doc.add_heading("7.4 Interpretation of Predictions (SHAP Explainability)", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("Using shap.TreeExplainer, we identified the top drivers governing intrusion predictions: src_bytes, count, dst_host_srv_count, and dst_bytes. In Case Study C (True Zero-Day attack 'snmpgetattack'), the classifier mistakenly predicted Normal with 99.99% confidence due to normal-looking byte rates, but the Isolation Forest flagged it as anomalous (score 0.58 vs threshold 0.49)—proving why hybrid routing is mandatory.")

    fig5_path = os.path.join(plots_dir, "shap_waterfall_case_c_-_true_zero-day_attack.png")
    if os.path.exists(fig5_path):
        doc.add_paragraph()
        doc.add_picture(fig5_path, width=Inches(5.0))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.add_run("Figure 5: SHAP Waterfall Plot for Case C — Revealing classifier confusion on a novel zero-day exploit.").italic = True

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 8: CONCLUSION & FUTURE WORK
    # =========================================================================
    h1 = doc.add_heading("8. Conclusion & Future Work", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(8)

    h2 = doc.add_heading("8.1 Summary of Learnings", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("This project proved that combining supervised classification with unsupervised anomaly detection bridges the gap between high accuracy on known signatures and resilience against zero-day intrusions. XGBoost achieved 77.9% multiclass accuracy on the realistic KDDTest+ benchmark, while Isolation Forest independently caught 63.1% of true zero-day attacks without seeing a single malicious training sample.")

    h2 = doc.add_heading("8.2 Technical and Domain Skills Acquired", level=2)
    skills_data = [
        ("Project Task", "Domain Category", "Specific Skill Acquired"),
        ("Data Exploration & Preprocessing", "Data Science & Security", "Pandas, One-Hot Encoding, StandardScaler, Leakage Prevention"),
        ("Supervised Classification", "Machine Learning", "XGBoost, Random Forest, Cost-Sensitive Loss Weighting, Multi-Class Profiling"),
        ("Zero-Day Anomaly Detection", "Unsupervised Learning", "Isolation Forest, Local Outlier Factor, PCA Reconstruction, Threshold Tuning"),
        ("Model Explainability", "Responsible / Transparent AI", "SHAP TreeExplainer, Beeswarm Plots, Waterfall Attribution Analysis"),
        ("Model Deployment", "MLOps & Cloud", "Streamlit UI Development, Joblib Serialization, GitHub Versioning, Cloud Hosting")
    ]
    tbl_sk = doc.add_table(rows=len(skills_data), cols=3)
    tbl_sk.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, row in enumerate(skills_data):
        for c_idx, val in enumerate(row):
            cell = tbl_sk.cell(idx, c_idx)
            set_cell_margins(cell, top=50, bottom=50, left=70, right=70)
            cell.paragraphs[0].add_run(val)
            if idx == 0:
                set_cell_background(cell, "E2E8F0")
                cell.paragraphs[0].runs[0].bold = True

    h2 = doc.add_heading("8.3 Limitations of the Current Approach", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("1. Offline Ingestion: Operates on pre-extracted feature vectors rather than streaming PCAP network flows.\n2. Extreme Minority Imbalance: R2L recall remains low (6%) due to novel payload variations in test data.\n3. Zero-Day Recall Headroom: A 63.1% standalone catch rate requires additional ensemble layering in production.")

    h2 = doc.add_heading("8.4 Future Scope", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("• Live Packet Sniffing: Integrate Zeek (Bro) or Suricata for real-time 41-feature extraction.\n• Streaming API: Containerize the pipeline with Docker and serve predictions via FastAPI.\n• Concept Drift Monitoring: Implement continual learning to dynamically adjust baseline profiles as enterprise traffic evolves.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 9: INTERNSHIP OUTCOMES
    # =========================================================================
    h1 = doc.add_heading("9. Internship Outcomes", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(8)

    h2 = doc.add_heading("9.1 Technical Skills Acquired", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("• Gained practical experience in end-to-end ML engineering (data loading, preprocessing, model fitting, and validation).\n• Mastered gradient boosted decision trees (XGBoost) and unsupervised isolation algorithms.\n• Developed interactive web applications using Streamlit and MLOps serialization using Joblib.\n• Gained hands-on experience in model explainability using SHAP.")

    h2 = doc.add_heading("9.2 Soft Skills Developed", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("• Analytical Thinking: Dissected why standard supervised models fail on novel attacks.\n• Communication & Documentation: Synthesized complex ML evaluations into professional engineering reports.\n• Time Management: Successfully delivered milestones on time across weekly sprints.")

    h2 = doc.add_heading("9.3 Contribution to Career Growth", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("This internship reinforced my academic foundation in CSE (AI & ML) with practical, industry-grade cybersecurity engineering skills. Building a complete, deployable hybrid intrusion detection system significantly boosts my technical proficiency and career readiness for data science, machine learning, and cybersecurity roles.")

    doc.add_page_break()

    # =========================================================================
    # APPENDIX
    # =========================================================================
    h1 = doc.add_heading("Appendix", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(8)

    h2 = doc.add_heading("A. Source Code", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("The complete source code, serialized models, and web application are available at:\n")
    p.add_run("GitHub Repository: ").bold = True
    p.add_run("https://github.com/mvssravan0-eng/IBMQ2DST2470_Prototype")

    h2 = doc.add_heading("B. Streamlit App Screenshots", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.add_run("The Streamlit web application allows users to simulate and inspect network connections in real time:")
    
    if os.path.exists(fig1_path):
        doc.add_picture(fig1_path, width=Inches(4.5))
    if os.path.exists(fig4_path):
        doc.add_picture(fig4_path, width=Inches(4.5))

    doc.add_page_break()

    h2 = doc.add_heading("C. Certificate of Completion", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(12)
    p.add_run("The certificate awarded for successful completion of the IBM Q2B Pearl Internship Program in Artificial Intelligence & Machine Learning (IBMQ2D Case Study #18, Application No: IBMQ2DST2470) is included below for reference:")

    cert_path = os.path.join(base_dir, "certificate.png")
    if os.path.exists(cert_path):
        p_cert = doc.add_paragraph()
        p_cert.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cert.paragraph_format.space_before = Pt(8)
        p_cert.paragraph_format.space_after = Pt(8)
        p_cert.add_run().add_picture(cert_path, width=Inches(6.2))

    for sec in doc.sections:
        add_page_borders(sec)

    output_path = os.path.join(base_dir, "IBMQ2DST2470_Internship_Case_Study_Report.docx")
    doc.save(output_path)
    print("Report generated successfully at:", output_path)

if __name__ == "__main__":
    build_document()

