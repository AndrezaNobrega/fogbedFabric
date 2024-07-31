#!/bin/bash
# Get docker sock path from environment variable
SOCK="${DOCKER_HOST:-/var/run/docker.sock}"
DOCKER_SOCK="${SOCK##unix://}"

#Formt echo
. scripts/utils.sh

CURRENT_DIR=$(pwd)
NETWORK_NAME=fabric_test

# Cria a rede Docker
echo "Criando a rede..."
docker network create ${NETWORK_NAME} || successln "A rede ${NETWORK_NAME} já existe, continuando..."

infoln "Gerando materiais criptograficos 🌀"
# Exportei o caminho do cryptogen, como var de ambiente.
cryptogen generate --config=./organizations/cryptogen/crypto-config-org1.yaml --output="organizations"
cryptogen generate --config=./organizations/cryptogen/crypto-config-org2.yaml --output="organizations"
cryptogen generate --config=./organizations/cryptogen/crypto-config-orderer.yaml --output="organizations"

echo "Iniciando o Orderer... 🍀"
# Iniciar o orderer
docker run -d --name orderer.example.com \
  -v "${CURRENT_DIR}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp:/var/hyperledger/orderer/msp" \
  -v "${CURRENT_DIR}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/:/var/hyperledger/orderer/tls" \
  -v "orderer.example.com:/var/hyperledger/production/orderer" \
  -v ${DOCKER_SOCK}:/host/var/run/docker.sock \
  -p 7050:7050 -p 7053:7053 -p 9443:9443 \
  --network ${NETWORK_NAME} \
  -e FABRIC_LOGGING_SPEC=INFO \
  -e ORDERER_GENERAL_LISTENADDRESS=0.0.0.0 \
  -e ORDERER_GENERAL_LISTENPORT=7050 \
  -e ORDERER_GENERAL_LOCALMSPID=OrdererMSP \
  -e ORDERER_GENERAL_LOCALMSPDIR=/var/hyperledger/orderer/msp \
  -e ORDERER_GENERAL_TLS_ENABLED=true \
  -e ORDERER_GENERAL_TLS_PRIVATEKEY=/var/hyperledger/orderer/tls/server.key \
  -e ORDERER_GENERAL_TLS_CERTIFICATE=/var/hyperledger/orderer/tls/server.crt \
  -e ORDERER_GENERAL_TLS_ROOTCAS=[/var/hyperledger/orderer/tls/ca.crt] \
  -e ORDERER_GENERAL_CLUSTER_CLIENTCERTIFICATE=/var/hyperledger/orderer/tls/server.crt \
  -e ORDERER_GENERAL_CLUSTER_CLIENTPRIVATEKEY=/var/hyperledger/orderer/tls/server.key \
  -e ORDERER_GENERAL_CLUSTER_ROOTCAS=[/var/hyperledger/orderer/tls/ca.crt] \
  -e ORDERER_GENERAL_BOOTSTRAPMETHOD=none \
  -e ORDERER_CHANNELPARTICIPATION_ENABLED=true \
  -e ORDERER_ADMIN_TLS_ENABLED=true \
  -e ORDERER_ADMIN_TLS_CERTIFICATE=/var/hyperledger/orderer/tls/server.crt \
  -e ORDERER_ADMIN_TLS_PRIVATEKEY=/var/hyperledger/orderer/tls/server.key \
  -e ORDERER_ADMIN_TLS_ROOTCAS=[/var/hyperledger/orderer/tls/ca.crt] \
  -e ORDERER_ADMIN_TLS_CLIENTROOTCAS=[/var/hyperledger/orderer/tls/ca.crt] \
  -e ORDERER_ADMIN_LISTENADDRESS=0.0.0.0:7053 \
  -e ORDERER_OPERATIONS_LISTENADDRESS=orderer.example.com:9443 \
  -e ORDERER_METRICS_PROVIDER=prometheus \
  -w /root \
  hyperledger/fabric-orderer:latest orderer

echo "Esperando 5 segundos antes de iniciar o Peer da Org1..."
# Esperar um pouco para garantir que o orderer esteja pronto antes de iniciar o peer
sleep 5

echo "Iniciando o Peer da Org1... 🍀 "
# Iniciar o peer da organização org1
docker run -d --name peer0.org1.example.com \
  -v "${CURRENT_DIR}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com:/etc/hyperledger/fabric" \
  -v peer0.org1.example.com:/var/hyperledger/production \
  -v "${CURRENT_DIR}/compose/docker/peercfg:/etc/hyperledger/peercfg" \
  -v ${DOCKER_SOCK}:/host/var/run/docker.sock \
  -v CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=${NETWORK_NAME} \
  -p 7051:7051 -p 9444:9444 \
  --network ${NETWORK_NAME} \
  -e CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=${NETWORK_NAME} \
  -e FABRIC_CFG_PATH=/etc/hyperledger/peercfg \
  -e FABRIC_LOGGING_SPEC=INFO \
  -e CORE_PEER_TLS_ENABLED=true \
  -e CORE_PEER_PROFILE_ENABLED=false \
  -e CORE_PEER_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt \
  -e CORE_PEER_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key \
  -e CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt \
  -e CORE_PEER_ID=peer0.org1.example.com \
  -e CORE_PEER_ADDRESS=peer0.org1.example.com:7051 \
  -e CORE_PEER_LISTENADDRESS=0.0.0.0:7051 \
  -e CORE_PEER_CHAINCODEADDRESS=peer0.org1.example.com:7052 \
  -e CORE_PEER_CHAINCODELISTENADDRESS=0.0.0.0:7052 \
  -e CORE_PEER_GOSSIP_BOOTSTRAP=peer0.org1.example.com:7051 \
  -e CORE_PEER_GOSSIP_EXTERNALENDPOINT=peer0.org1.example.com:7051 \
  -e CORE_PEER_LOCALMSPID=Org1MSP \
  -e CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp \
  -e CORE_OPERATIONS_LISTENADDRESS=peer0.org1.example.com:9444 \
  -e CORE_METRICS_PROVIDER=prometheus \
  -e CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock \
  -e CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG={"peername":"peer0org1"} \
  -e CORE_CHAINCODE_EXECUTETIMEOUT=300s \
  -w /root \
  hyperledger/fabric-peer:latest peer node start

echo "Esperando 5 segundos antes de iniciar o Peer da Org2..."
# Esperar um pouco para garantir que o peer da org1 esteja pronto antes de iniciar o peer da org2
sleep 5

echo "Iniciando o Peer da Org2... 🍀"
# Iniciar o peer da organização org2
docker run -d --name peer0.org2.example.com \
  -v ${CURRENT_DIR}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com:/etc/hyperledger/fabric \
  -v peer0.org2.example.com:/var/hyperledger/production \
  -v "${CURRENT_DIR}/compose/docker/peercfg:/etc/hyperledger/peercfg" \
  -v ${DOCKER_SOCK}:/host/var/run/docker.sock \
  -v CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=${NETWORK_NAME} \
  -p 9051:9051 -p 9445:9445 \
  --network ${NETWORK_NAME} \
  -e FABRIC_CFG_PATH=/etc/hyperledger/peercfg \
  -e FABRIC_LOGGING_SPEC=INFO \
  -e CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=${NETWORK_NAME} \
  -e CORE_PEER_TLS_ENABLED=true \
  -e CORE_PEER_PROFILE_ENABLED=false \
  -e CORE_PEER_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt \
  -e CORE_PEER_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key \
  -e CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt \
  -e CORE_PEER_ID=peer0.org2.example.com \
  -e CORE_PEER_ADDRESS=peer0.org2.example.com:9051 \
  -e CORE_PEER_LISTENADDRESS=0.0.0.0:9051 \
  -e CORE_PEER_CHAINCODEADDRESS=peer0.org2.example.com:9052 \
  -e CORE_PEER_CHAINCODELISTENADDRESS=0.0.0.0:9052 \
  -e CORE_PEER_GOSSIP_EXTERNALENDPOINT=peer0.org2.example.com:9051 \
  -e CORE_PEER_GOSSIP_BOOTSTRAP=peer0.org2.example.com:9051 \
  -e CORE_PEER_LOCALMSPID=Org2MSP \
  -e CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp \
  -e CORE_OPERATIONS_LISTENADDRESS=peer0.org2.example.com:9445 \
  -e CORE_METRICS_PROVIDER=prometheus \
  -e CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock \
  -e CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG={"peername":"peer0org2"} \
  -e CORE_CHAINCODE_EXECUTETIMEOUT=300s \
  -w /root \
  hyperledger/fabric-peer:latest peer node start

echo "Iniciando o Cliente CLI interativo... 🍀"
# Iniciar o cliente CLI interativo
docker run -it --rm --name cli \
  -w /opt/gopath/src/github.com/hyperledger/fabric/peer \
  -e GOPATH=/opt/gopath \
  -e FABRIC_LOGGING_SPEC=INFO \
  -e FABRIC_CFG_PATH=/etc/hyperledger/peercfg \
  -v "${CURRENT_DIR}/compose/docker/peercfg:/etc/hyperledger/peercfg" \
  -v ${CURRENT_DIR}/organizations:/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations \
  -v ${CURRENT_DIR}/scripts:/opt/gopath/src/github.com/hyperledger/fabric/peer/scripts/ \
  -e CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock \
  -v ${DOCKER_SOCK}:/host/var/run/docker.sock \
  --network ${NETWORK_NAME} \
  hyperledger/fabric-tools:latest


infoln "Criando o canal 🌀"


echo "Script concluído."
