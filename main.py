import sys
import os
import json
import base64

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QTextEdit, 
                             QCheckBox, QLabel, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap

class ImageDropPanel(QLabel):
    """Custom panel for dropping and holding images."""
    image_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Drag and drop image files here") 
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                background-color: #f9f9f9;
                color: #555;
            }
        """)
        self.setAcceptDrops(True)
        self.current_image_path = ""

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toLocalFile()
            ext = os.path.splitext(url)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        url = event.mimeData().urls()[0].toLocalFile()
        self.current_image_path = url
        
        pixmap = QPixmap(url)
        self.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        self.image_dropped.emit(url)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gemma Multimodal Client") 
        self.resize(650, 880)
        
        self.setting_file_path = "setting_load_image.json"
        # To prevent accidental change events during settings loading
        self._block_signals = False  
        
        self.init_ui()
        self.connect_signals()
        self.load_settings()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Model file path
        self.label_model_file_path = QLabel("Model File Path")
        main_layout.addWidget(self.label_model_file_path)

        model_layout = QHBoxLayout()
        self.textbox_model_file_path = QLineEdit()
        # Model file path (.gguf)
        self.textbox_model_file_path.setPlaceholderText("Model file path (.gguf)") 
        # Browse...
        self.button_get_model_file_path = QPushButton("Browse...") 
        model_layout.addWidget(self.textbox_model_file_path)
        model_layout.addWidget(self.button_get_model_file_path)
        main_layout.addLayout(model_layout)

        # 2. mmproj file path
        self.label_mmproj_file_path = QLabel("Mmproj File Path")
        main_layout.addWidget(self.label_mmproj_file_path)

        mmproj_layout = QHBoxLayout()
        self.textbox_mmproj_file_path = QLineEdit()
        # Mmproj file path (mmproj-*.gguf)
        self.textbox_mmproj_file_path.setPlaceholderText("Mmproj file path (mmproj-*.gguf)") 
        # Browse...
        self.button_get_mmproj_file_path = QPushButton("Browse...")
        mmproj_layout.addWidget(self.textbox_mmproj_file_path)
        mmproj_layout.addWidget(self.button_get_mmproj_file_path)
        main_layout.addLayout(mmproj_layout)

        # Prompt input area
        main_layout.addWidget(QLabel("Prompt String:")) 
        self.textbox_prompt_string = QTextEdit()
        # Enter your prompt/instructions
        self.textbox_prompt_string.setPlaceholderText("Enter your prompt/instructions") 
        self.textbox_prompt_string.setMaximumHeight(80)
        main_layout.addWidget(self.textbox_prompt_string)

        # Image drop panel
        main_layout.addWidget(QLabel("Input Image (D&D Area):")) 
        self.panel_get_image = ImageDropPanel()
        self.panel_get_image.setMinimumHeight(200)
        main_layout.addWidget(self.panel_get_image)

        # Options and Clipboard operations area
        opt_layout = QHBoxLayout()
        # Auto-copy result
        self.checkbox_auto_copy_result = QCheckBox("Auto Copy Result") 
        # Use CUDA (GPU)
        self.checkbox_use_cuda = QCheckBox("Use CUDA (GPU)") # Default checked for GPU priority
        self.checkbox_use_cuda.setChecked(True) 
        # Copy result
        self.button_copy_result = QPushButton("Copy Result")
        # Save settings
        self.button_save_setting = QPushButton("Save Settings")
        self.button_save_setting.setEnabled(False)  # Disabled initially
        
        opt_layout.addWidget(self.checkbox_auto_copy_result)
        opt_layout.addWidget(self.checkbox_use_cuda)
        opt_layout.addWidget(self.button_copy_result)
        opt_layout.addWidget(self.button_save_setting)
        main_layout.addLayout(opt_layout)

        # Settings rename/load buttons area
        setting_btn_layout = QHBoxLayout()
        # Save settings as a different name...
        self.button_save_setting_as = QPushButton("Save Settings As...") 
        # Load from specified setting file...
        self.button_load_setting_from = QPushButton("Load From File...") 
        setting_btn_layout.addWidget(self.button_save_setting_as)
        setting_btn_layout.addWidget(self.button_load_setting_from)
        main_layout.addLayout(setting_btn_layout)

        # Inference result output area
        main_layout.addWidget(QLabel("Output Result:"))
        self.textbox_result_string = QTextEdit()
        self.textbox_result_string.setReadOnly(True)
        main_layout.addWidget(self.textbox_result_string)

    def connect_signals(self):
        # Change detection signals (including checkbox_use_cuda)
        self.textbox_model_file_path.textChanged.connect(self.on_control_changed)
        self.textbox_mmproj_file_path.textChanged.connect(self.on_control_changed)
        self.textbox_prompt_string.textChanged.connect(self.on_control_changed)
        self.checkbox_auto_copy_result.stateChanged.connect(self.on_control_changed)
        self.checkbox_use_cuda.stateChanged.connect(self.on_control_changed) 

        # Button events
        self.button_get_model_file_path.clicked.connect(self.select_model_file)
        self.button_get_mmproj_file_path.clicked.connect(self.select_mmproj_file)
        self.button_copy_result.clicked.connect(self.copy_result_to_clipboard)
        self.button_save_setting.clicked.connect(self.save_settings)
        
        # Save/Load signals
        self.button_save_setting_as.clicked.connect(self.save_settings_as)
        self.button_load_setting_from.clicked.connect(self.load_settings_from)

        # Image drag and drop event
        self.panel_get_image.image_dropped.connect(self.run_inference)

    def on_control_changed(self):
        if not self._block_signals:
            self.button_save_setting.setEnabled(True)

    def select_model_file(self):
        file_filter = "GGUF Files (*.gguf);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Model File", "", file_filter
        )
        if file_path:
            self.textbox_model_file_path.setText(file_path)

    def select_mmproj_file(self):
        file_filter = "GGUF Files (*.gguf);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Mmproj File", "", file_filter
        )
        if file_path:
            self.textbox_mmproj_file_path.setText(file_path)

    def copy_result_to_clipboard(self):
        text = self.textbox_result_string.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def _get_current_settings_dict(self):
        return {
            "model_file_path": self.textbox_model_file_path.text(),
            "mmproj_file_path": self.textbox_mmproj_file_path.text(),
            "prompt_string": self.textbox_prompt_string.toPlainText(),
            "auto_copy_result": self.checkbox_auto_copy_result.isChecked(),
            "use_cuda": self.checkbox_use_cuda.isChecked() 
        }

    def save_settings(self):
        settings = self._get_current_settings_dict()
        try:
            with open(self.setting_file_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            self.button_save_setting.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{e}")

    def save_settings_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Settings As", "", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return
            
        settings = self._get_current_settings_dict()
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "Success", "Settings saved successfully with a different name.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings under a different name:\n{e}")

    def _apply_settings_dict(self, settings):
        self._block_signals = True
        if "model_file_path" in settings:
            self.textbox_model_file_path.setText(settings["model_file_path"])
        if "mmproj_file_path" in settings:
            self.textbox_mmproj_file_path.setText(settings["mmproj_file_path"])
        if "prompt_string" in settings:
            self.textbox_prompt_string.setPlainText(settings["prompt_string"])
        if "auto_copy_result" in settings:
            self.checkbox_auto_copy_result.setChecked(settings["auto_copy_result"])
        if "use_cuda" in settings: 
            self.checkbox_use_cuda.setChecked(settings["use_cuda"])
        self._block_signals = False
        self.button_save_setting.setEnabled(False)

    def load_settings(self):
        if not os.path.exists(self.setting_file_path):
            return
        try:
            with open(self.setting_file_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            self._apply_settings_dict(settings)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to load settings file:\n{e}")
            self._block_signals = False

    def load_settings_from(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Settings File", "", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            self._apply_settings_dict(settings)
            QMessageBox.information(self, "Success", "Settings file loaded successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load settings file:\n{e}")

    def convert_image_to_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        ext = os.path.splitext(image_path)[1].lower().replace('.', '')
        if ext == 'jpg': ext = 'jpeg'
        return f"data:image/{ext};base64,{encoded_string}"

    def run_inference(self, image_path):
        model_path = self.textbox_model_file_path.text()
        mmproj_path = self.textbox_mmproj_file_path.text()
        prompt = self.textbox_prompt_string.toPlainText()

        if not model_path or not os.path.exists(model_path):
            QMessageBox.warning(self, "Error", "Please specify a valid model file path.")
            return
        
        if not mmproj_path or not os.path.exists(mmproj_path):
            QMessageBox.warning(self, "Error", "Please specify a valid mmproj file path.")
            return

        # Switch GPU layer assignment based on checkbox state
        if self.checkbox_use_cuda.isChecked():
            gpu_layers = -1
            device_msg = "Running inference on GPU (CUDA)..."
        else:
            gpu_layers = 0  # Setting to 0 means no GPU usage, fully CPU driven
            device_msg = "Running inference on CPU... (May take time)"

        self.textbox_result_string.setPlainText("Initializing AI module...")
        QApplication.processEvents()

        llm = None
        try:
            from llama_cpp import Llama
            from llama_cpp.llama_chat_format import Llava15ChatHandler

            self.textbox_result_string.setPlainText(device_msg)
            QApplication.processEvents()

            # Initialize chat handler with paths
            chat_handler = Llava15ChatHandler(
                clip_model_path=mmproj_path, 
                verbose=False
            )
            
            # n_gpu_layers (0 or -1) is applied to both LLM and Vision models
            llm = Llama(
                model_path=model_path, 
                chat_handler=chat_handler,
                n_ctx=4096,
                n_gpu_layers=gpu_layers,
                chat_format="gemma",
                verbose=True
            )

            image_data_uri = self.convert_image_to_base64(image_path)
            user_prompt = prompt.strip() if prompt.strip() else "Describe the content of this image in detail."
            # Ensure prompt is handled correctly for encoding/decoding safety, although unnecessary after stripping empty string check
            user_prompt = str(user_prompt.encode('utf-8', 'ignore').decode('utf-8'))

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": image_data_uri}}
                    ]
                }
            ]

            response = llm.create_chat_completion(
                messages=messages,
                temperature=0.2,
                max_tokens=1024
            )
            
            result_text = response["choices"][0]["message"]["content"]
            self.textbox_result_string.setPlainText(result_text)

            if self.checkbox_auto_copy_result.isChecked():
                self.copy_result_to_clipboard()

        except Exception as e:
            self.textbox_result_string.setPlainText(f"An error occurred during inference:\n{e}")
        
        finally:
            if llm is not None:
                try:
                    if hasattr(llm, 'close'):
                        llm.close()
                except Exception:
                    pass
                del llm
            
            import gc
            gc.collect()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())
