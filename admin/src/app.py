import gradio as gr

import db
from core import scrape_pages

with gr.Blocks(title="Samfundet Admin") as admin_page:
    gr.Markdown("# Admin Dashboard")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Queue Stats")
            stat_disp = gr.JSON(value=db.get_stats)
            refresh_btn = gr.Button("Refresh Stats")
            reset_processing_btn = gr.Button("Reset Processing", variant="stop")
            reset_failed_btn = gr.Button("Reset Failed", variant="stop")
            reset_out = gr.Textbox(label="Reset Result", lines=3)
            refresh_btn.click(db.get_stats, outputs=stat_disp)
            reset_processing_btn.click(db.reset_processing, outputs=reset_out)
            reset_failed_btn.click(db.reset_failed, outputs=reset_out)
        
        with gr.Column():
            gr.Markdown("### Scraper")
            s_in = gr.Number(value=0, label="Start Page")
            e_in = gr.Number(value=5, label="End Page")
            scrape_btn = gr.Button("Add Pages to Queue", variant="primary")
            log_out = gr.Textbox(label="Logs", lines=10)

            scrape_btn.click(scrape_pages, [s_in, e_in], log_out)

if __name__ == "__main__":
    admin_page.launch()
