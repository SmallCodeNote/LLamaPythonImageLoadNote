# Setup
## Model Source
https://huggingface.co/bartowski/google_gemma-4-E4B-it-GGUF/tree/main
google_gemma-4-E4B-it-Q8_0.gguf
mmproj-google_gemma-4-E4B-it-f16.gguf

## Python Version 
python 3.12.10 Embeddable **(Installation location: .\python)**

## Edit .\python\python312._pth
**Uncomment `#import site` to make it `import site`.** 

## Terminal Command
.\python\python.exe -m pip install https://github.com/abetlen/llama-cpp-python/releases/download/v0.3.23-cu124/llama_cpp_python-0.3.23-py3-none-win_amd64.whl --no-cache-dir --force-reinstall

# GUI
## Control List
- label_model_file_path="Model file path"
- textbox_model_file_path
- button_get_model_file_path
- label_mmproj_file_path="Mmproj file path"
- textbox_mmproj_file_path
- button_get_mmproj_file_path 
- textbox_prompt_string
- textbox_result_string
- checkbox_auto_copy_result
- checkbox_use_cuda
- button_copy_result
- button_save_setting
- button_save_setting_as
- button_load_setting_from
- panel_get_image

## Operation
*   Upon startup, if the file ".\setting_load_image.json" exists, its content will be read and reflected in the controls. If a control does not have a corresponding entry in the JSON, **that control remains unchanged.** (または: *no action is taken for that control.*)

*   The `button_save_setting` is typically disabled. It becomes enabled when the value of any control changes.

*   When an image file (jpeg, jpg, png, gif) is dragged and dropped onto `panel_get_image`, **the model processes the input** using a prompt combined with the image, and the result is stored in `textbox_result_string`.

*   The functionality of other controls has been implemented using event codes corresponding to their respective names.
