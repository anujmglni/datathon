"""
PDF & Document Export Service for KSP Platform.
Converts markdown reports and case summaries into styled PDF documents.
"""

import os
import time

def generate_pdf_report(title: str, markdown_content: str) -> dict:
    """
    Renders styled HTML wrapper around markdown_content and exports PDF.
    """
    timestamp = int(time.time())
    output_filename = f"ksp_report_{timestamp}.pdf"
    
    # Simple HTML compilation with Weasyprint fallback
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                margin: 2cm;
                @top-center {{
                    content: "KARNATAKA POLICE - CONFIDENTIAL CRIME INTELLIGENCE REPORT";
                    font-family: 'Helvetica', sans-serif;
                    font-size: 8pt;
                    color: #718096;
                }}
                @bottom-center {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-family: 'Helvetica', sans-serif;
                    font-size: 8pt;
                    color: #718096;
                }}
            }}
            body {{
                font-family: 'Helvetica', sans-serif;
                color: #2D3748;
                line-height: 1.6;
            }}
            h1 {{ color: #1A365D; border-bottom: 2px solid #2B6CB0; padding-bottom: 5px; }}
            h2 {{ color: #2C5282; margin-top: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ border: 1px solid #CBD5E0; padding: 8px; text-align: left; }}
            th {{ background-color: #E2E8F0; color: #2D3748; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div>{markdown_content.replace('\n', '<br>')}</div>
    </body>
    </html>
    """

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=full_html).write_pdf()
        return {
            "success": True,
            "filename": output_filename,
            "html_preview": full_html[:500],
            "size_bytes": len(pdf_bytes)
        }
    except Exception as e:
        print(f"⚠️ Weasyprint unavailable fallback: {e}")
        return {
            "success": True,
            "filename": output_filename,
            "html_preview": full_html,
            "note": "Rendered to HTML wrapper fallback"
        }
