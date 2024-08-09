from fogbed import FogbedExperiment, setLogLevel
from fabric_plugin import FabricPlugin
import time
import random

setLogLevel('info')

# Configurações específicas para sua rede Hyperledger Fabric
exp = FogbedExperiment()
fabric_plugin = FabricPlugin(exp)

# Criação da instância virtual para o Orderer
cloud = exp.add_virtual_instance('cloud')

# Iniciar o Orderer
orderer = fabric_plugin.add_orderer(
    name='orderer',
    environment={
        'FABRIC_LOGGING_SPEC': 'DEBUG',
        'ORDERER_GENERAL_LISTENADDRESS': '0.0.0.0',
        'ORDERER_GENERAL_LISTENPORT': '7050',
        'ORDERER_GENERAL_LOCALMSPID': 'OrdererMSP',
        'ORDERER_GENERAL_LOCALMSPDIR': '/var/hyperledger/orderer/msp',
        'ORDERER_GENERAL_TLS_ENABLED': 'true',
        'ORDERER_GENERAL_TLS_PRIVATEKEY': '/var/hyperledger/orderer/tls/server.key',
        'ORDERER_GENERAL_TLS_CERTIFICATE': '/var/hyperledger/orderer/tls/server.crt',
        'ORDERER_GENERAL_TLS_ROOTCAS': '/var/hyperledger/orderer/tls/ca.crt',
        'ORDERER_GENERAL_CLUSTER_CLIENTCERTIFICATE': '/var/hyperledger/orderer/tls/server.crt',
        'ORDERER_GENERAL_CLUSTER_CLIENTPRIVATEKEY': '/var/hyperledger/orderer/tls/server.key',
        'ORDERER_GENERAL_CLUSTER_ROOTCAS': '/var/hyperledger/orderer/tls/ca.crt',
        'ORDERER_GENERAL_BOOTSTRAPMETHOD': 'none',
        'ORDERER_CHANNELPARTICIPATION_ENABLED': 'true',
        'ORDERER_ADMIN_TLS_ENABLED': 'true',
        'ORDERER_ADMIN_TLS_CERTIFICATE': '/var/hyperledger/orderer/tls/server.crt',
        'ORDERER_ADMIN_TLS_PRIVATEKEY': '/var/hyperledger/orderer/tls/server.key',
        'ORDERER_ADMIN_TLS_ROOTCAS': '/var/hyperledger/orderer/tls/ca.crt',
        'ORDERER_ADMIN_TLS_CLIENTROOTCAS': '/var/hyperledger/orderer/tls/ca.crt',
        'ORDERER_ADMIN_LISTENADDRESS': '0.0.0.0:7053',
        'ORDERER_OPERATIONS_LISTENADDRESS': 'mn.orderer:9443',
        'ORDERER_METRICS_PROVIDER': 'prometheus',
    },
    volumes=[
        '/home/nobrega/Desktop/fabric-test/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp:/var/hyperledger/orderer/msp',
        '/home/nobrega/Desktop/fabric-test/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls:/var/hyperledger/orderer/tls',
        'orderer.example.com:/var/hyperledger/production/orderer',
    ],
    port_bindings={'7050': 7050, '7053': 7053, '9443': 9443},
    network_mode='fabric_test'
)

# Criação da instância virtual para o Peer da Org1
org1 = exp.add_virtual_instance('org1')

# Iniciar o Peer da Org1
peer0_org1 = fabric_plugin.add_peer(
    name='peer0.org1',
    environment={
        'FABRIC_CFG_PATH': '/etc/hyperledger/peercfg',
        'FABRIC_LOGGING_SPEC': 'DEBUG',
        'CORE_PEER_TLS_ENABLED': 'true',
        'CORE_PEER_PROFILE_ENABLED': 'false',
        'CORE_PEER_TLS_CERT_FILE': '/etc/hyperledger/fabric/tls/server.crt',
        'CORE_PEER_TLS_KEY_FILE': '/etc/hyperledger/fabric/tls/server.key',
        'CORE_PEER_TLS_ROOTCERT_FILE': '/etc/hyperledger/fabric/tls/ca.crt',
        'CORE_PEER_ID': 'peer0.org1.example.com',
        'CORE_PEER_ADDRESS': 'peer0.org1.example.com:7051',
        'CORE_PEER_LISTENADDRESS': '0.0.0.0:7051',
        'CORE_PEER_CHAINCODEADDRESS': 'peer0.org1.example.com:7052',
        'CORE_PEER_CHAINCODELISTENADDRESS': '0.0.0.0:7052',
        'CORE_PEER_GOSSIP_BOOTSTRAP': 'peer0.org1.example.com:7051',
        'CORE_PEER_GOSSIP_EXTERNALENDPOINT': 'peer0.org1.example.com:7051',
        'CORE_PEER_LOCALMSPID': 'Org1MSP',
        'CORE_PEER_MSPCONFIGPATH': '/etc/hyperledger/fabric/msp',
        'CORE_OPERATIONS_LISTENADDRESS': 'mn.peer0.org1:9444',
        'CORE_METRICS_PROVIDER': 'prometheus',
        'CORE_VM_ENDPOINT': 'unix:///host/var/run/docker.sock',
        'CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE': 'fabric_test',
        'CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG': '{"peername":"peer0org1"}',
        'CORE_CHAINCODE_EXECUTETIMEOUT': '300s',
    },
    volumes=[
        '/home/nobrega/Desktop/fabric-test/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com:/etc/hyperledger/fabric:rw',
        'peer0.org1.example.com:/var/hyperledger/production:rw',
        '/home/nobrega/Desktop/fabric-test/fabric-samples/test-network/compose/docker/peercfg:/etc/hyperledger/peercfg:rw',
        '/var/run/docker.sock:/host/var/run/docker.sock:rw',
    ],
    port_bindings={'7051': 7051, '9444': 9444},
    org_instance=org1,
    network_mode='fabric_test'
)

# Criação da instância virtual para o Peer da Org2
org2 = exp.add_virtual_instance('org2')
# Iniciar o Peer da Org2
peer0_org2 = fabric_plugin.add_peer(
    name='peer0.org2',
    environment={
        'FABRIC_CFG_PATH': '/etc/hyperledger/peercfg',
        'FABRIC_LOGGING_SPEC': 'DEBUG',
        'CORE_PEER_TLS_ENABLED': 'true',
        'CORE_PEER_PROFILE_ENABLED': 'false',
        'CORE_PEER_TLS_CERT_FILE': '/etc/hyperledger/fabric/tls/server.crt',
        'CORE_PEER_TLS_KEY_FILE': '/etc/hyperledger/fabric/tls/server.key',
        'CORE_PEER_TLS_ROOTCERT_FILE': '/etc/hyperledger/fabric/tls/ca.crt',
        'CORE_PEER_ID': 'peer0.org2.example.com',
        'CORE_PEER_ADDRESS': 'peer0.org2.example.com:9051',
        'CORE_PEER_LISTENADDRESS': '0.0.0.0:9051',
        'CORE_PEER_CHAINCODEADDRESS': 'peer0.org2.example.com:9052',
        'CORE_PEER_CHAINCODELISTENADDRESS': '0.0.0.0:9052',
        'CORE_PEER_GOSSIP_BOOTSTRAP': 'peer0.org2.example.com:9051',
        'CORE_PEER_GOSSIP_EXTERNALENDPOINT': 'peer0.org2.example.com:9051',
        'CORE_PEER_LOCALMSPID': 'Org2MSP',
        'CORE_PEER_MSPCONFIGPATH': '/etc/hyperledger/fabric/msp',
        'CORE_OPERATIONS_LISTENADDRESS': 'mn.peer0.org2:9445',
        'CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE': 'fabric_test',
        'CORE_METRICS_PROVIDER': 'prometheus',
        'CORE_VM_ENDPOINT': 'unix:///host/var/run/docker.sock',
        'CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG': '{"peername":"peer0org2"}',
        'CORE_CHAINCODE_EXECUTETIMEOUT': '300s',
    },
    volumes=[
        '/home/nobrega/Desktop/fabric-test/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com:/etc/hyperledger/fabric:rw',
        'peer0.org2.example.com:/var/hyperledger/production:rw',
        '/home/nobrega/Desktop/fabric-test/fabric-samples/test-network/compose/docker/peercfg:/etc/hyperledger/peercfg:rw',
        '/var/run/docker.sock:/host/var/run/docker.sock:rw',
    ],
    port_bindings={'9051': 9051, '9445': 9445},
    org_instance=org2,
    network_mode='fabric_test'
)


# Iniciar a experimentação
try:
    print("Iniciando a experimentação...")
    exp.start()
    print("Containerers na rede. 🌱")
    
    # Verificar o status dos containers
    time.sleep(5)  # Aguarde alguns segundos para garantir que os containers tenham tempo para iniciar
    containers = exp.get_containers()
    print("Containers rodando:", containers)

    # Criar o canal
    var = random.randint(1, 99999)
    channel_name = "teste"+ str(var)
    print(f"Criando o canal {channel_name} 🐙")
    try:
        result = fabric_plugin.create_channel(channel_name=channel_name)
        print(result)
    except Exception as e:
        print(e)


    # Aguardar a entrada do usuário antes de parar a experimentação
    input("Pressione Enter para parar a experimentação...")

finally:
    exp.stop()
    print("Experimentação parada. 🚫")
