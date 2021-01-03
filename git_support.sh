# Script to automatically commit support files to GIT

# Acceleration files
git add \*.acc > /dev/null
git commit --quiet -m "acc files ~ unimportant" > /dev/null

# DXF files
git add \*.dxf > /dev/null
git commit --quiet -m "dxf files ~ unimportant" > /dev/null

# Pickles files
git add \*.pkl > /dev/null
git commit --quiet -m "pkl files ~ unimportant" > /dev/null

# VS code  files
git add ./.vscode/*
git commit --quiet -m "vscode files ~ unimportant" > /dev/null

# Sh files
git add \*.sh > /dev/null
git commit --quiet -m "shell files ~ unimportant" > /dev/null

# Environment control
git add Pipfile > /dev/null
git add Pipfile.lock > /dev/null
git commit --quiet -m "venv files ~ unimportant" > /dev/null

# Print commits ahead 
git log origin..HEAD
