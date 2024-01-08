#!/bin/bash

cd "$(dirname "$0")"

cd AetherNode
source venv/bin/activate
python3 Download_Model.py




python3 AetherNode_ExLlama2.py

cd ..



# If missing requirements
# sudo add-apt-repository universe
# sudo apt update
# sudo apt install python3-pip


# pip install unzip
# wget http://www.libraryofcelsus.com/wp-content/uploads/2023/11/run_AetherNode_linux.zip
# unzip experimental_linux_AetherNode_install_script.zip
# chmod +x script_name.sh
# ./experimental_linux_AetherNode_install_script.sh