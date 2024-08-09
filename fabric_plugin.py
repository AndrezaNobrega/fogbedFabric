from fogbed import Container
import os
from subprocess import check_output, CalledProcessError
import time
from colored_printer import successln, errorln, warningln

class FabricPlugin:
    def __init__(self, exp):
        self.exp = exp
        self.containers = {}

    def add_orderer(self, name, environment, volumes, port_bindings, network_mode):
        container = Container(
            name=name,
            dimage='larsid/fogbed-fabric-orderer:2.5-custom-1',
            environment=environment,
            volumes=volumes,
            port_bindings=port_bindings,
            network_mode=network_mode,
            dcmd='orderer start',
        )
        self.exp.add_docker(container, self.exp.get_virtual_instance('cloud'))
        self.containers[name] = container
        return container

    def add_peer(self, name, environment, volumes, port_bindings, org_instance, network_mode):
        container = Container(
            name=name,
            dimage='larsid/fogbed-fabric-peer:2.5-custom-1',
            environment=environment,
            volumes=volumes,
            port_bindings=port_bindings,
            network_mode=network_mode,
            dcmd='peer node start',
        )
        self.exp.add_docker(container, org_instance)
        self.containers[name] = container
        return container

    def create_channel(self, channel_name):
        print('Executando a criação do canal...')
        os.makedirs("channel-artifacts", exist_ok=True)

        CLI_DELAY = 3
        MAX_RETRY = 5

        configtxgen_path = "/home/nobrega/Desktop/fabric-samples/bin/configtxgen"

        if not os.path.isfile(configtxgen_path) or not os.access(configtxgen_path, os.X_OK):
            raise Exception(f"Configtxgen binary not found or not executable at {configtxgen_path}")

        profile = "ChannelUsingRaft"
        ROOTDIR = os.getcwd()

        env = os.environ.copy()
        
    
        env['FABRIC_CFG_PATH'] = f"{ROOTDIR}/configtx"
        print('Criando o bloco gênesis... 🌱')
        genesis_block_cmd = [
            configtxgen_path,
            "-profile", profile,
            "-outputBlock", f"./channel-artifacts/{channel_name}.block",
            "-channelID", channel_name
        ]

        try:
            print(f"Running command: {' '.join(genesis_block_cmd)}")
            output = check_output(genesis_block_cmd, env=env)
            successln(f"Channel genesis block '{channel_name}.block' generated successfully.")
            print(output.decode())
        except CalledProcessError as e:
            errorln(f"Error output: {e.output.decode()}")
            raise Exception(f"Failed to generate channel configuration transaction: {e.output.decode()}")

        ROOTDIR = os.getcwd()
        ORDERER_ADMIN_TLS_SIGN_CERT = f"{ROOTDIR}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt"
        ORDERER_ADMIN_TLS_PRIVATE_KEY = f"{ROOTDIR}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.key"
        ORDERER_CA = f"{ROOTDIR}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt"

        if not all(os.path.isfile(f) for f in [ORDERER_ADMIN_TLS_SIGN_CERT, ORDERER_ADMIN_TLS_PRIVATE_KEY, ORDERER_CA]):
            raise Exception("One or more TLS files are missing or not accessible")

        osnadmin_path = "/home/nobrega/Desktop/fabric-samples/bin/osnadmin"
        print(f'Juntando orderer ao canal {channel_name}')
        osnadmin_cmd = [
            osnadmin_path,
            "channel", "join",
            "--channelID", channel_name,
            "--config-block", f"./channel-artifacts/{channel_name}.block",
            "-o", "localhost:7053",
            "--ca-file", ORDERER_CA,
            "--client-cert", ORDERER_ADMIN_TLS_SIGN_CERT,
            "--client-key", ORDERER_ADMIN_TLS_PRIVATE_KEY
        ]

        try:
            print(f"Running command: {' '.join(osnadmin_cmd)}")
            output = check_output(osnadmin_cmd, env=env)
            successln(f"Channel '{channel_name}' created successfully.")
            print(output.decode())
        except CalledProcessError as e:
            errorln(f"Error output: {e.output.decode()}")
            raise Exception(f"Channel creation failed: {e.output.decode()}")

        for org in [1, 2]:
            self.join_channel(org, channel_name, MAX_RETRY, CLI_DELAY)
            self.set_anchor_peer(org, channel_name)

        return f"Channel '{channel_name}' created and joined"

    def join_channel(self, org, channel_name, max_retry, cli_delay):
        print('Executando Join Channel')
        ROOTDIR = os.getcwd()
        ORDERER_CA = f"{ROOTDIR}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt"
        

        blockfile = f"{ROOTDIR}/channel-artifacts/{channel_name}.block"
        peer_path = "/home/nobrega/Desktop/fabric-samples/bin/peer"

        env = os.environ.copy()
        env['FABRIC_CFG_PATH'] = f"{ROOTDIR}/configtx"

        # aqui o que eu coloquei p resolver o
        os.environ['CORE_PEER_TLS_ENABLED'] = 'true'
        os.environ['CORE_PEER_LOCALMSPID'] = 'Org1MSP'
        os.environ['CORE_PEER_TLS_ROOTCERT_FILE'] = f'{os.getcwd()}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'
        os.environ['CORE_PEER_MSPCONFIGPATH'] = f'{os.getcwd()}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp'
        os.environ['CORE_PEER_ADDRESS'] = 'localhost:7051'

        
        print('Buscando o bloco de configuração do canal no orderer...')
        peer_cmd = [
            peer_path, "channel", "fetch", "0", blockfile,
            "-o", "localhost:7050",
            "--ordererTLSHostnameOverride", "orderer.example.com",
            "-c", channel_name,
            "--tls", "--cafile", ORDERER_CA
        ]

        try:
            print(f"Running command: {' '.join(peer_cmd)}")
            output = check_output(peer_cmd)
            print(output.decode())
        except CalledProcessError as e:
            print(f"Error output: {e.output.decode()}")
            

        join_cmd = [peer_path, "channel", "join", "-b", blockfile]
        env = os.environ.copy()
        env['CORE_PEER_LOCALMSPID'] = f"Org{org}MSP"
        env['CORE_PEER_TLS_ROOTCERT_FILE'] = f"{ROOTDIR}/organizations/peerOrganizations/org{org}.example.com/peers/peer0.org{org}.example.com/tls/ca.crt"
        env['CORE_PEER_MSPCONFIGPATH'] = f"{ROOTDIR}/organizations/peerOrganizations/org{org}.example.com/users/Admin@org{org}.example.com/msp"
        env['CORE_PEER_ADDRESS'] = f"localhost:7051"

        counter = 1
        while counter <= max_retry:
            try:
                print(f"Running command: {' '.join(join_cmd)} (attempt {counter})")
                output = check_output(join_cmd, env=env)
                print(f"Peer0.org{org} joined channel '{channel_name}' successfully.")
                print(output.decode())
                break
            except CalledProcessError as e:
                print(f"Error output: {e.output.decode()}")
                counter += 1
                if counter > max_retry:
                    raise Exception(f"After {max_retry} attempts, peer0.org{org} has failed to join channel '{channel_name}'")
                else:
                    time.sleep(cli_delay)

    def set_anchor_peer(self, org, channel_name):
        print('Executando o comando se ancho peer')
        set_anchor_peer_cmd = ["./scripts/setAnchorPeer.sh", str(org), channel_name]
        try:
            print(f"Running command: {' '.join(set_anchor_peer_cmd)}")
            output = check_output(set_anchor_peer_cmd)
            print(f"Anchor peer for org{org} set successfully.")
            print(output.decode())
        except CalledProcessError as e:
            print(f"Error output: {e.output.decode()}")
            raise Exception(f"Failed to set anchor peer for org{org}: {e.output.decode()}")
