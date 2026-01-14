"""
GUI Dialogs Module - V3.0
Diálogos para interface gráfica
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QCheckBox
)
from PyQt6.QtCore import Qt

# ===========================================
# 1. PAGE SELECTION DIALOG
# ===========================================

class PageSelectionDialog(QDialog):
    """Dialog para seleção interativa de páginas (Spider Mode)"""

    def __init__(self, pages: list[dict], parent=None):
        """Inicializa dialog de seleção

        Args:
            pages: Lista de páginas [{"url": "...", "title": "...", "selected": True}]
            parent: Janela pai
        """
        super().__init__(parent)
        self.pages = pages
        self.selected_pages = []

        self.setWindowTitle("Selecionar Páginas para Download")
        self.setMinimumSize(800, 600)
        self._setup_ui()
        self._populate_list()

    def _setup_ui(self):
        """Configura layout do dialog"""
        layout = QVBoxLayout(self)

        # Cabeçalho
        header = QLabel(
            f"<h3>📑 {len(self.pages)} Páginas Encontradas</h3>"
            "<p>Selecione as páginas que deseja baixar.</p>"
        )
        layout.addWidget(header)

        # Botões de seleção
        btn_layout = QHBoxLayout()
        self.chk_select_all = QCheckBox("Selecionar Todos")
        self.chk_select_all.setChecked(True)
        self.chk_select_all.toggled.connect(self._toggle_all)

        btn_layout.addWidget(self.chk_select_all)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Lista de páginas (com checkboxes)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # Botões de ação
        action_layout = QHBoxLayout()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_confirm = QPushButton("Confirmar Seleção")
        self.btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px;
            }
        """)
        self.btn_confirm.clicked.connect(self._confirm_selection)

        action_layout.addWidget(self.btn_cancel)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_confirm)
        layout.addLayout(action_layout)

    def _populate_list(self):
        """Popula lista com páginas encontradas"""
        for page in self.pages:
            item = QListWidgetItem()
            item.setText(f"📄 {page['title']}\n   {page['url']}")
            item.setData(Qt.ItemDataRole.UserRole, page)
            item.setCheckState(Qt.CheckState.Checked)  # Default: marcado
            self.list_widget.addItem(item)

    def _toggle_all(self, checked: bool):
        """Marca/desmarca todos os itens"""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(state)

    def _confirm_selection(self):
        """Coleta páginas marcadas e fecha dialog"""
        selected = []

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                page = item.data(Qt.ItemDataRole.UserRole)
                selected.append(page)

        self.selected_pages = selected
        self.accept()

    def get_selected_pages(self) -> list[dict]:
        """Retorna páginas selecionadas pelo usuário"""
        return self.selected_pages