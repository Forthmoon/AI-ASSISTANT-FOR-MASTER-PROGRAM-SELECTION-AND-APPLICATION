import yaml
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.sql import text
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import sys
logging.basicConfig(level=logging.ERROR)
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


if project_root not in sys.path:
    sys.path.insert(0, project_root)


db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/genai.db"))

db_uri = f"sqlite:///{db_path}"


engine = create_engine(db_uri)
Session = scoped_session(sessionmaker(bind=engine))

def fetch_multiple_program_details(selected_items):
    """
    Retrieve complete details of multiple programs from the SQLite database and assemble them into a nested data structure.
    Fixed the 'tuple indices must be integers' issue by using .mappings() to return dictionary-style results.
    """
    try:
        # ========== A. Validate input ==========
        if not selected_items or not isinstance(selected_items, list):
            raise ValueError("Invalid input: expected a list of university_id and program_id pairs.")

        main_conditions = " OR ".join(
            [f"(p.university_id = :u{i} AND p.program_id = :p{i})"
             for i, _ in enumerate(selected_items)]
        )
        doc_conditions = " OR ".join(
            [f"(rd.program_id = :p{i})"
             for i, _ in enumerate(selected_items)]
        )

        params = {}
        for i, item in enumerate(selected_items):
            params[f"u{i}"] = item["university_id"]
            params[f"p{i}"] = item["program_id"]

        main_query = text(f"""
            SELECT
                p.program_id,
                p.university_id,
                p.program_name,
                p.focus,
                p.application_link,
                p.program_duration,
                p.city,
                p.application_deadline,
                p.tuition_fee,
                u.university AS univ_name,
                sq.qs_ranking,

                a.bachelor_major,
                a.gpa_min,
                a.completed_ects,
                a.additional_conditions AS application_conditions,

                COALESCE((
                  SELECT GROUP_CONCAT(
                    rm.module_name || ': ' || rm.required_credits || ' ECTS',
                    '; '
                  )
                  FROM required_modules rm
                  WHERE rm.program_id = p.program_id
                ), '') AS module_name,

                l.ielts_score,
                l.toefl_score,
                l.german_score,
                l.alternative_certificate
            FROM programs p
            JOIN university_info u ON p.university_id = u.university_id
            LEFT JOIN subject_qs_ranking sq ON sq.subject_id = p.subject_id
                                           AND sq.university_id = p.university_id
            LEFT JOIN academic_requirements a ON p.program_id = a.program_id
            LEFT JOIN language_requirements l ON p.program_id = l.program_id
            WHERE {main_conditions}
        """)

        doc_query = text(f"""
            SELECT
                rd.program_id,
                rd.document_name,
                rd.is_mandatory,
                rd.notes
            FROM required_documents rd
            WHERE {doc_conditions}
        """)

        with Session() as session:
            main_rows = session.execute(main_query, params).mappings().all()
            doc_rows = session.execute(doc_query, params).mappings().all()

        if not main_rows:
            return {"message": "No programs found for the selected criteria."}

        # organize documents
        docs_map = {}
        for row in doc_rows:
            pid = row["program_id"]
            if pid not in docs_map:
                docs_map[pid] = []
            # 0 -> False / 1 -> True
            mandatory_bool = (row["is_mandatory"] == 1)
            docs_map[pid].append({
                "document_name": row["document_name"] or "",
                "is_mandatory": mandatory_bool,
                "notes": row["notes"] or ""
            })

        # university distribution
        uni_map = {}
        for row in main_rows:
            uid = row["university_id"]
            if uid not in uni_map:
                uni_map[uid] = {
                    "university": row["univ_name"] if row["univ_name"] else "Unknown University",
                    "programs": []
                }

            pid = row["program_id"]
            qs_rank = str(row["qs_ranking"]) if row["qs_ranking"] is not None else "N/A"

            gpa_str = str(row["gpa_min"]) if row["gpa_min"] is not None else ""
            ects_str = str(row["completed_ects"]) if row["completed_ects"] is not None else ""

            program_dict = {
                "program_name": row["program_name"] or "",
                "focus": row["focus"] or "",
                "application_conditions": row["application_conditions"] or "",
                "application_link": row["application_link"] or "",
                "program_duration": row["program_duration"] or "",
                "city": row["city"] or "",
                "application_deadline": row["application_deadline"] or "",
                "tuition_fee": row["tuition_fee"] or "",
                "qs_ranking": qs_rank,

                "academic_requirements": {
                    "bachelor_major": row["bachelor_major"] or "",
                    "gpa_min": gpa_str,
                    "completed_ects": ects_str,
                    "module_name": row["module_name"] or ""
                },
                "language_requirements": {
                    "ielts_score": str(row["ielts_score"]) if row["ielts_score"] else "N/A",
                    "toefl_score": str(row["toefl_score"]) if row["toefl_score"] else "N/A",
                    "german_score": str(row["german_score"]) if row["german_score"] else "N/A",
                    "alternative_certificate": row["alternative_certificate"] or "N/A"
                },
                "application_documents": docs_map.get(pid, [])
            }

            uni_map[uid]["programs"].append(program_dict)

        # turn to list
        final_list = []
        for uid, data in uni_map.items():
            final_list.append({
                "university": data["university"],
                "programs": data["programs"]
            })

        return final_list

    except Exception as e:
        logging.error("Error fetching program details: %s", str(e))
        return {"error": "An unexpected error occurred. Please try again later."}

def generate_university_comparison_pdf(data, output_file):
    """
    Generate a "University and Program Comparison" report in PDF format, including:
  - Cover Page: Title and generation time (excluding preview tables).
  - Table of Contents: Based on university and program names.
  - Main Content: Lists each program under its respective university.
    * "Focus," "Additional Application Conditions," and "Application Link" are bolded titles.
    * Row 1: "Basic Info" (gray column) & "Academic Req" (gray column) side by side;
      uses KeepTogether to prevent page breaks.
    * Row 2: "Language Requirements" (header in the first row); uses KeepTogether.
    * Row 3: "Application Documents" (header in the first row);
      the "Document Name" column width is increased to 4/3 of the original; uses KeepTogether.
"""


    pdf_doc = SimpleDocTemplate(output_file, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']

    # ----------- cover page -------------
    elements.append(Spacer(1, 100))
    title = Paragraph(
        "<para align='center'><font size=24><b>University and Program Comparison Report</b></font></para>",
        styles['Title']
    )
    elements.append(title)

    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_para = Paragraph(
        f"<para align='center'><font size=12>Generated on: {date_str}</font></para>",
        styles['Normal']
    )
    elements.append(Spacer(1, 30))
    elements.append(date_para)
    elements.append(PageBreak())

    # ----------- catalog page -------------
    elements.append(Paragraph("<b>Table of Contents</b>", styles['Heading1']))
    for university in data:
        university_name = university['university']
        elements.append(Paragraph(f"<font size=14><b>{university_name}</b></font>", styles['Heading1']))
        for program in university['programs']:
            program_name = program['program_name']
            link_html = f"<a href='#{program_name}'>{program_name}</a>"
            elements.append(Paragraph(link_html, normal_style))
    elements.append(PageBreak())

    # ----------- content -------------
    for university in data:
        university_name = university['university']
        elements.append(Paragraph(f"<b>{university_name}</b>", styles['Heading1']))

        for program in university['programs']:
            program_name = program['program_name']

            # Focus、Additional Conditions、Application Link加粗标题
            focus = program.get('focus', 'N/A')
            additional_conditions = program.get('additional_conditions', 'N/A')
            application_link = program.get('application_link', 'N/A')

            # Second Title
            elements.append(Paragraph(f"<a name='{program_name}'/><b>{program_name}</b>", styles['Heading2']))
            
            # Focus
            elements.append(Paragraph(f"<b>Focus:</b> {focus}", normal_style))

            # Additional Conditions
            elements.append(Paragraph(f"<b>Additional Application Conditions:</b> {additional_conditions}", normal_style))

            # Application Link
            if application_link != 'N/A':
                link_html = f"<link href='{application_link}'>{application_link}</link>"
                elements.append(Paragraph(f"<b>Application Link:</b> {link_html}", normal_style))
            
            elements.append(Spacer(1, 10))

            # ========== First Line ==========
            basic_acad_block = []
            basic_acad_block.append(Paragraph(
                "Below are the basic details of the program, along with the key academic requirements you must meet:",
                normal_style
            ))
            basic_acad_block.append(Spacer(1, 10))

            # -- Basic Information
            basic_info_data = [
                ["Program Duration", Paragraph(program.get('program_duration', 'N/A'), normal_style)],
                ["City", Paragraph(program.get('city', 'N/A'), normal_style)],
                ["Application Deadline", Paragraph(program.get('application_deadline', 'N/A'), normal_style)],
                ["Tuition Fee", Paragraph(program.get('tuition_fee', 'N/A'), normal_style)],
                ["QS Ranking (Subject)", Paragraph(program.get('qs_ranking', 'N/A'), normal_style)]
            ]
            basic_info_table = Table(basic_info_data, colWidths=[120, 120])
            basic_info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
                ('SPLITLONGWORDS', (0, 0), (-1, -1), True),
            ]))

            # -- Academic Requirements
            academic_req = program.get('academic_requirements', {})
            academic_requirements_data = [
                ["Bachelor Major", Paragraph(academic_req.get('bachelor_major', 'N/A'), normal_style)],
                ["GPA Min", Paragraph(academic_req.get('gpa_min', 'N/A'), normal_style)],
                ["Completed ECTS", Paragraph(academic_req.get('completed_ects', 'N/A'), normal_style)],
                ["Module Name", Paragraph(academic_req.get('module_name', 'N/A'), normal_style)]
            ]
            academic_requirements_table = Table(academic_requirements_data, colWidths=[120, 120])
            academic_requirements_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
                ('SPLITLONGWORDS', (0, 0), (-1, -1), True),
            ]))

            basic_flow = [
                Paragraph("<b>Basic Information</b>", styles['Heading3']),
                Spacer(1, 5),
                basic_info_table
            ]
            academic_flow = [
                Paragraph("<b>Academic Requirements</b>", styles['Heading3']),
                Spacer(1, 5),
                academic_requirements_table
            ]
            top_table = Table([[basic_flow, academic_flow]], colWidths=[260, 260])
            top_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))

            basic_acad_block.append(top_table)
            basic_acad_block.append(Spacer(1, 20))

            # use KeepTogether
            elements.append(KeepTogether(basic_acad_block))

            # ========== Second Line ==========
            lang_block = []
            lang_block.append(Paragraph(
                "Below are the language requirements for this program. The first row is the header:",
                normal_style
            ))
            lang_block.append(Spacer(1, 10))

            language_req = program.get('language_requirements', {})
            lr_col_widths = [81, 81, 81, 277]
            language_requirements_data = [
                ["IELTS Score", "TOEFL Score", "German Score", "Alternative Certificate"],
                [
                    Paragraph(language_req.get('ielts_score', 'N/A'), normal_style),
                    Paragraph(language_req.get('toefl_score', 'N/A'), normal_style),
                    Paragraph(language_req.get('german_score', 'N/A'), normal_style),
                    Paragraph(language_req.get('alternative_certificate', 'N/A'), normal_style)
                ]
            ]
            language_requirements_table = Table(language_requirements_data, colWidths=lr_col_widths)
            language_requirements_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
                ('SPLITLONGWORDS', (0, 0), (-1, -1), True),
            ]))

            lr_title = Paragraph("<b>Language Requirements</b>", styles['Heading3'])
            lr_block_table = Table([
                [lr_title],
                [language_requirements_table]
            ], colWidths=[520])
            lr_block_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))

            lang_block.append(lr_block_table)
            lang_block.append(Spacer(1, 20))
            elements.append(KeepTogether(lang_block))

            # ==========Third Line==========
            doc_block = []
            doc_block.append(Paragraph(
                "Finally, here are the application documents required. The first row is the header:",
                normal_style
            ))
            doc_block.append(Spacer(1, 10))

            app_docs = program.get('application_documents', [])
            ad_col_widths = [133, 75, 312]
            application_documents_data = [["Document Name", "Mandatory", "Notes"]]
            for doc in app_docs:
                application_documents_data.append([
                    Paragraph(doc.get('document_name', 'N/A'), normal_style),
                    Paragraph("Yes" if doc.get('is_mandatory') else "No", normal_style),
                    Paragraph(doc.get('notes', 'N/A'), normal_style)
                ])

            app_docs_table = Table(application_documents_data, colWidths=ad_col_widths)
            app_docs_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
                ('SPLITLONGWORDS', (0, 0), (-1, -1), True),
            ]))

            ad_title = Paragraph("<b>Application Documents</b>", styles['Heading3'])
            ad_block_table = Table([
                [ad_title],
                [app_docs_table]
            ], colWidths=[520])
            ad_block_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))

            doc_block.append(ad_block_table)
            doc_block.append(Spacer(1, 20))
            elements.append(KeepTogether(doc_block))

            elements.append(PageBreak())

    # generate PDF
    pdf_doc.build(elements)
    print(f"PDF generated: {output_file}")