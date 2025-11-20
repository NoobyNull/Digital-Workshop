from pathlib import Path
text = Path('src/gui/CLO/cut_list_optimizer_widget.py').read_text()
start = text.index('# Add + button (column 6)')
end = text.index('self.ui_refs["pieces_table"].setCellWidget(row, 6, add_container)') + len('self.ui_refs["pieces_table"].setCellWidget(row, 6, add_container)')
print(text[start:end])
