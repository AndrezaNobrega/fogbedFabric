#!/bin/bash

echo ++++++++++++++++++++++++++++++++++++++++++++++++++
echo Rodando o script orderer.sh
echo ++++++++++++++++++++++++++++++++++++++++++++++++++

channel_name=$1

# Exibir o nome do canal
echo "Nome do canal: ${channel_name}"

# Configuração das variáveis de ambiente
echo "Configurando variáveis de ambiente..."
export PATH=${ROOTDIR}/../bin:${PWD}/../bin:$PATH
echo "PATH configurado: $PATH"

export ORDERER_ADMIN_TLS_SIGN_CERT=${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt
echo "Certificado TLS do Orderer: $ORDERER_ADMIN_TLS_SIGN_CERT"

export ORDERER_ADMIN_TLS_PRIVATE_KEY=${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.key
echo "Chave privada TLS do Orderer: $ORDERER_ADMIN_TLS_PRIVATE_KEY"

# Verificar se os arquivos de certificado e chave existem
if [ ! -f "$ORDERER_ADMIN_TLS_SIGN_CERT" ]; then
    echo "Erro: Certificado TLS do Orderer não encontrado em $ORDERER_ADMIN_TLS_SIGN_CERT" >&2
    exit 1
fi

if [ ! -f "$ORDERER_ADMIN_TLS_PRIVATE_KEY" ]; then
    echo "Erro: Chave privada TLS do Orderer não encontrada em $ORDERER_ADMIN_TLS_PRIVATE_KEY" >&2
    exit 1
fi

# Exibir informações sobre o bloco de configuração
BLOCKFILE="./channel-artifacts/${channel_name}.block"
echo "Arquivo de bloco de configuração: $BLOCKFILE"
if [ ! -f "$BLOCKFILE" ]; then
    echo "Erro: Arquivo de bloco de configuração não encontrado em $BLOCKFILE" >&2
    exit 1
fi

# Executar o comando osnadmin para juntar o orderer ao canal
echo "Juntando o orderer ao canal ${channel_name}..."
osnadmin channel join --channelID ${channel_name} --config-block $BLOCKFILE -o localhost:7053 --ca-file "$ORDERER_CA" --client-cert "$ORDERER_ADMIN_TLS_SIGN_CERT" --client-key "$ORDERER_ADMIN_TLS_PRIVATE_KEY" >> log.txt 2>&1

# Verificar o resultado do comando osnadmin
if [ $? -ne 0 ]; then
    echo "Erro: Falha ao executar o comando osnadmin. Verifique o arquivo log.txt para mais detalhes." >&2
    exit 1
else
    echo "Orderer adicionado ao canal ${channel_name} com sucesso."
fi

# Exibir o conteúdo do arquivo de log
echo "Conteúdo do arquivo log.txt:"
cat log.txt
