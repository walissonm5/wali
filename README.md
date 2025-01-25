
#!/bin/bash

# Nome do usuário do GitHub e nome do repositório
GITHUB_USER="walissonm5"
REPO_NAME="wali"

# Caminho do repositório local
LOCAL_REPO_PATH="walissonm5/walissonm2/wali"

# Mensagem do commit inicial
INITIAL_COMMIT_MSG="Primeiro commit"

# URL do repositório remoto
REMOTE_URL="https://github.com/$GITHUB_walissonm5/$REPO_wali.git"

# Configurando Git
git config --global user.name "walissonm2"
git config --global user.email "reiswalisson75@gmail.com"

# Criando o repositório local
mkdir -p $LOCAL_REPO_PATH
cd $LOCAL_REPO_PATH
git init

# Adicionando um arquivo README.md
echo "# $REPO_NAME" > README.md
git add README.md

# Fazendo o commit inicial
git commit -m "$INITIAL_COMMIT_MSG"

# Adicionando o repositório remoto
git remote add origin $REMOTE_URL

# Fazendo push para o repositório remoto
git push -u origin master

echo "Repositório $REPO_NAME conectado ao GitHub com sucesso!"
