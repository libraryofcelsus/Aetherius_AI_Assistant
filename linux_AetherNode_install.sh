#!/bin/bash

cd "$(dirname "$0")"

# Install Cuda if not installed
# https://developer.nvidia.com/cuda-downloads
sudo apt-get update
sudo apt-get install -y jq
pip install virtualenv   
# Setup Python virtual environment

# Clone the AetherNode repository and switch to the specified branch
git clone https://github.com/libraryofcelsus/AetherNode --branch 0.06
cd AetherNode
python3 -m virtualenv venv2
source venv2/bin/activate
pip install -r requirements.txt
pip install bitsandbytes accelerate scipy
pip install transformers>=4.32.0 optimum>=1.12.0
pip install 'auto-gptq==0.5.1'
pip install 'exllamav2==0.0.9'
pip install 'flask==3.0.0'
pip install jq
cd ..

# If missing requirements
# sudo add-apt-repository universe
# sudo apt update
# sudo apt install python3-pip


# pip install unzip
# wget http://www.libraryofcelsus.com/wp-content/uploads/2023/11/experimental_linux_AetherNode_install_script.zip
# unzip experimental_linux_AetherNode_install_script.zip
# chmod +x script_name.sh
# ./experimental_linux_AetherNode_install_script.sh