@echo off
REM Change directory to the script's location
cd %~dp0

git clone https://github.com/libraryofcelsus/AetherNode --branch 0.06

cd AetherNode

REM Create a virtual environment named 'venv'
python -m venv venv

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Install requirements from requirements.txt
pip install -r requirements.txt

REM The following line assumes you have CUDA 11.8 installed, change it if you have a different version
REM Please visit https://pytorch.org/get-started/locally/ to find the correct install command for your CUDA version
pip install torch torchvision torchaudio -f https://download.pytorch.org/whl/torch_stable.html


REM Install specific versions of transformers and optimum
pip install transformers>=4.32.0 optimum>=1.12.0

REM Uninstall auto-gptq if it was previously installed
pip uninstall -y auto-gptq

REM Clone the AutoGPTQ repository and install it
git clone https://github.com/PanQiWei/AutoGPTQ
cd AutoGPTQ
pip install .

cd ..

git clone https://github.com/turboderp/exllamav2
cd exllamav2
pip install .

echo Setup is complete.
pause
