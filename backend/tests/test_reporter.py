from pathlib import Path
import tempfile

from reporter import Reporter


def test_render_report_html_smoke():
    with tempfile.TemporaryDirectory() as d:
        rep = Reporter(Path('backend/templates'))
        dummy = {
            'run_id': 'rid',
            'dataset_id': 'ds',
            'model_spec': 'ollama:llama3.2:2b',
            'conversations': [
                {
                    'conversation_id': 'c1',
                    'summary': { 'conversation_pass': True, 'weighted_pass_rate': 0.9, 'final_outcome': {'pass': True, 'reasons': []} },
                    'turns_transcript': [
                        {'index': 1, 'role': 'user', 'text': 'Hi'},
                        {'index': 2, 'role': 'assistant', 'text': 'Hello'}
                    ],
                    'turns': [
                        {'turn_index': 1, 'metrics': { 'exact': {'pass': True}}}
                    ]
                }
            ]
        }
        html = rep.render_html(dummy)
        assert '<html>' in html and 'Run rid — Evaluation Report' in html
        out = Path(d) / 'report.html'
        rep.write_html(dummy, out)
        assert out.exists() and out.read_text(encoding='utf-8').startswith('<!doctype html>')
