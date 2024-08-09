#!/bin/bash
#
# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

# Este script foi projetado para ser executado pelo addOrg3.sh como o
# segundo passo do tutorial de Adicionando uma Organização a um Canal.
# Ele junta os peers da org3 ao canal previamente configurado no
# tutorial da rede de teste.

CHANNEL_NAME="$1"
DELAY="$2"
TIMEOUT="$3"
VERBOSE="$4"
: ${CHANNEL_NAME:="mychannel"}
: ${DELAY:="3"}
: ${TIMEOUT:="10"}
: ${VERBOSE:="false"}
COUNTER=1
MAX_RETRY=5

# importar variáveis de ambiente
# variável home da rede de teste aponta para a pasta test-network
# o motivo de usarmos uma variável aqui é considerar a pasta específica da org3
# ao invocar isso para org3 como test-network/scripts/org3-scripts
# o valor é alterado de padrão como $PWD (test-network)
# para ${PWD}/.. para fazer a importação funcionar

infoln ++++++++++++++++++++++++++++++++++++++++++++++++++
infoln "Rodando o script joinChannel.sh"
infoln ++++++++++++++++++++++++++++++++++++++++++++++++++

export TEST_NETWORK_HOME="${PWD}/.."
. ${TEST_NETWORK_HOME}/scripts/envVar.sh

# joinChannel ORG
joinChannel() {
  ORG=$1
  setGlobals $ORG
  local rc=1
  local COUNTER=1
  ## Às vezes o Join leva tempo, portanto retry
  while [ $rc -ne 0 -a $COUNTER -lt $MAX_RETRY ] ; do
    sleep $DELAY
    set -x
    peer channel join -b $BLOCKFILE >&log.txt
    res=$?
    { set +x; } 2>/dev/null
    let rc=$res
    COUNTER=$(expr $COUNTER + 1)
  done
  cat log.txt
  verifyResult $res "Após $MAX_RETRY tentativas, o peer0.org${ORG} falhou ao juntar-se ao canal '$CHANNEL_NAME'"
}

setAnchorPeer() {
  ORG=$1
  ${TEST_NETWORK_HOME}/scripts/setAnchorPeer.sh $ORG $CHANNEL_NAME
}

setGlobals 3
BLOCKFILE="${TEST_NETWORK_HOME}/channel-artifacts/${CHANNEL_NAME}.block"

echo "Buscando o bloco de configuração do canal no orderer..."
set -x
peer channel fetch 0 $BLOCKFILE -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com -c $CHANNEL_NAME --tls --cafile "$ORDERER_CA" >&log.txt
res=$?
{ set +x; } 2>/dev/null
cat log.txt
verifyResult $res "Busca do bloco de configuração no orderer falhou"

infoln "Juntando o peer da org3 ao canal..."
joinChannel 3

infoln "Configurando o peer âncora para a org3..."
setAnchorPeer 3

successln "Canal '$CHANNEL_NAME' unido"
successln "Peer da Org3 adicionado com sucesso à rede"
