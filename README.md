Please view the Wiki here for contextual information:

https://github.com/H3yfinn/transport_model_9th_edition/wiki

## SETUP
There are two options for environments. They depend if you want to use jupyter or just the command line to run the model. I prefer to use jupyter but i know that it takes a lot of space/set-up-time.
 - config/env_jupyter.yml
 - config/env_no_jupyter.yml

run:
conda env create --prefix ./env_jupyter --file ./config/env_jupyter.yml

Then:
conda activate ./env_jupyter

Note that installing those libraries in the yml files will result in a few other dependencies also being installed.

## Run the model
Simply put, if using the command line, just use:
python integrate.py

If using Jupyter with Visual Studio Code, you can run the .py files cell by cell as separated by the #%% characters. I'm not sure how the #%% thing works outside of Visual Studio Code.

## Documentation
There are some documentation files in ./documentation/. They can be used in addition to the Wiki.

## Folder structure
./workflow/ - inside here are the files you need to run the model. 
./other_code/ - inside here is extra code that is useful to use for visualisation of the outputs, creation of input data and some kinds of analysis/exploration files. 
./config/ - general configurations you can set, other than those that are in the integrate.py file.