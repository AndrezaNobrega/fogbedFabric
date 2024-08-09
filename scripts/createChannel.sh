#!/bin/bash

# Importações
. scripts/envVar.sh

CHANNEL_NAME="$1"
DELAY="$2"
MAX_RETRY="$3"
VERBOSE="$4"
BFT="$5"
: ${CHANNEL_NAME:="mychannel"}
: ${DELAY:="3"}
: ${MAX_RETRY:="5"}
: ${VERBOSE:="false"}
: ${BFT:=0}

: ${CONTAINER_CLI:="docker"}
if command -v ${CONTAINER_CLI}-compose > /dev/null 2>&1; then
    : ${CONTAINER_CLI_COMPOSE:="${CONTAINER_CLI}-compose"}
else
    : ${CONTAINER_CLI_COMPOSE:="${CONTAINER_CLI} compose"}
fi
infoln "Usando ${CONTAINER_CLI} e ${CONTAINER_CLI_COMPOSE}"

if [ ! -d "channel-artifacts" ]; then
    infoln "Diretório 'channel-artifacts' não encontrado. Criando diretório..."
    mkdir channel-artifacts
fi

createChannelGenesisBlock() {
  setGlobals 1
  which configtxgen
  if [ "$?" -ne 0 ]; then
    fatalln "Ferramenta configtxgen não encontrada. Certifique-se de que o binário está no PATH."
  fi
  local bft_true=$1
  infoln "Gerando bloco de gênese para o canal com a configuração BFT=${bft_true}..."
  set -x

  if [ $bft_true -eq 1 ]; then
    infoln "Chamando configtxgen com o perfil ChannelUsingBFT..."
    configtxgen -profile ChannelUsingBFT -outputBlock ./channel-artifacts/${CHANNEL_NAME}.block -channelID $CHANNEL_NAME
    infoln "Bloco de gênese gerado usando o perfil BFT: ${CHANNEL_NAME}.block"
  else
    infoln "Chamando configtxgen com o perfil ChannelUsingRaft..."
    configtxgen -profile ChannelUsingRaft -outputBlock ./channel-artifacts/${CHANNEL_NAME}.block -channelID $CHANNEL_NAME
    infoln "Bloco de gênese gerado usando o perfil Raft: ${CHANNEL_NAME}.block"
  fi
  res=$?
  { set +x; } 2>/dev/null
  if [ $res -ne 0 ]; then
    fatalln "Falha ao gerar a transação de configuração do canal. Verifique o arquivo de log para mais detalhes."
  fi
}

createChannel() {
  # Poll para o caso do líder do raft ainda não estar definido
  local rc=1
  local COUNTER=1
  local bft_true=$1
  infoln "Adicionando orderers ao canal ${CHANNEL_NAME}..."
  while [ $rc -ne 0 -a $COUNTER -lt $MAX_RETRY ] ; do
    infoln "Tentativa $COUNTER de $MAX_RETRY para adicionar orderers..."
    sleep $DELAY
    set -x
    infoln "Chamando scripts/orderer.sh..."
    . scripts/orderer.sh ${CHANNEL_NAME}
    if [ $bft_true -eq 1 ]; then
      infoln "Chamando scripts/orderer2.sh..."
      . scripts/orderer2.sh ${CHANNEL_NAME}
      infoln "Chamando scripts/orderer3.sh..."
      . scripts/orderer3.sh ${CHANNEL_NAME}
      infoln "Chamando scripts/orderer4.sh..."
      . scripts/orderer4.sh ${CHANNEL_NAME}
      infoln "Orderers BFT adicionados ao canal ${CHANNEL_NAME}."
    else
      infoln "Orderers Raft adicionados ao canal ${CHANNEL_NAME}."
    fi
    res=$?
    { set +x; } 2>/dev/null
    let rc=$res
    COUNTER=$(expr $COUNTER + 1)
  done
  if [ $rc -ne 0 ]; then
    fatalln "Falha na criação do canal após $MAX_RETRY tentativas. Verifique o arquivo de log para mais detalhes."
  fi
}

# joinChannel ORG
joinChannel() {
  ORG=$1
  #será que eh isso aqui? não
  FABRIC_CFG_PATH=$PWD/../config/
  setGlobals $ORG
  local rc=1
  local COUNTER=1
  infoln "Tentando juntar o peer da organização ${ORG} ao canal ${CHANNEL_NAME}..."
  ## Às vezes o Join leva tempo, portanto retry
  while [ $rc -ne 0 -a $COUNTER -lt $MAX_RETRY ] ; do
    infoln "Tentativa $COUNTER de $MAX_RETRY para juntar o peer ao canal..."
    sleep $DELAY
    set -x
    infoln "Chamando peer channel join..."
    peer channel join -b $BLOCKFILE >&log.txt
    res=$?
    { set +x; } 2>/dev/null
    if [ $res -ne 0 ]; then
      infoln "Falha ao juntar o peer ao canal. Verifique o arquivo de log (log.txt) para mais detalhes."
    fi
    let rc=$res
    COUNTER=$(expr $COUNTER + 1)
  done
  cat log.txt
  if [ $rc -ne 0 ]; then
    fatalln "Após $MAX_RETRY tentativas, o peer0.org${ORG} falhou ao juntar-se ao canal '$CHANNEL_NAME'."
  else
    infoln "Peer da organização ${ORG} juntado ao canal com sucesso."
  fi
}

setAnchorPeer() {
  ORG=$1
  infoln "Configurando o peer âncora para a organização ${ORG} no canal ${CHANNEL_NAME}..."
  infoln "Chamando scripts/setAnchorPeer.sh com parâmetros: $ORG $CHANNEL_NAME"
  . scripts/setAnchorPeer.sh $ORG $CHANNEL_NAME 
  infoln "Peer âncora para a organização ${ORG} configurado com sucesso."
}

## O usuário tenta usar o orderer BFT na rede Fabric com CA
if [ $BFT -eq 1 ] && [ -d "organizations/fabric-ca/ordererOrg/msp" ]; then
  fatalln "A rede Fabric parece estar usando CA. Este exemplo ainda não suporta o uso de consenso BFT e CA juntos."
fi

## Criar bloco de gênese do canal
FABRIC_CFG_PATH=$PWD/../config/
BLOCKFILE="./channel-artifacts/${CHANNEL_NAME}.block"

infoln "Gerando bloco de gênese do canal '${CHANNEL_NAME}.block'"
FABRIC_CFG_PATH=${PWD}/configtx
if [ $BFT -eq 1 ]; then
  FABRIC_CFG_PATH=${PWD}/bft-config
fi
createChannelGenesisBlock $BFT

infoln ++++++++++++++++++++++++++++++++++++++++++++++++++
infoln "Rodando o script createChannel.sh"
infoln ++++++++++++++++++++++++++++++++++++++++++++++++++

## Criar canal
infoln "Criando canal ${CHANNEL_NAME}"
createChannel $BFT
successln "Canal '$CHANNEL_NAME' criado com sucesso"

## Juntar todos os peers ao canal
infoln "Juntando o peer da org1 ao canal..."
joinChannel 1
infoln "Juntando o peer da org2 ao canal..."
joinChannel 2

## Configurar os peers âncoras para cada organização no canal
infoln "Configurando o peer âncora para org1..."
setAnchorPeer 1
infoln "Configurando o peer âncora para org2..."
setAnchorPeer 2

successln "Canal '$CHANNEL_NAME' associado com sucesso"
