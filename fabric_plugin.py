from fogbed import Container
import os
from subprocess import check_output, CalledProcessError
import time
from colored_printer import successln, errorln, warningln
import subprocess
import json

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
    
    def create_docker_network(self, network_name):
        # Verifica se a rede já existe
        try:
            output = subprocess.check_output(['docker', 'network', 'ls'])
            if network_name in output.decode():
                print(f"A rede '{network_name}' já existe.")
                return
        except subprocess.CalledProcessError as e:
            print(f"Erro ao listar redes Docker: {e}")
            print(f"Saída de erro: {e.output.decode()}")
            return

        print(f"Criando a rede Docker '{network_name}'...")
        command = ['docker', 'network', 'create', network_name]

        try:
            subprocess.run(command, check=True)
            print(f"Rede '{network_name}' criada com sucesso.")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao criar a rede Docker: {e}")
            print(f"Saída de erro: {e.output.decode()}")

    def generate_crypto_materials(self):
        print("Gerando materiais criptográficos 🌀")
        self.create_docker_network('fabric_test')
        
        # Caminho para o diretório onde estão as configurações de cryptogen
        crypto_config_path = "./organizations/cryptogen"
        
        # Caminho absoluto para o binário cryptogen
        cryptogen_path = "/home/nobrega/Desktop/fabric-samples/bin/cryptogen"
        
        # Comandos para gerar materiais criptográficos
        commands = [
            f"{cryptogen_path} generate --config={crypto_config_path}/crypto-config-org1.yaml --output=organizations",
            f"{cryptogen_path} generate --config={crypto_config_path}/crypto-config-org2.yaml --output=organizations",
            f"{cryptogen_path} generate --config={crypto_config_path}/crypto-config-orderer.yaml --output=organizations"
        ]
        
        # Executando cada comando
        for command in commands:
            print(f"Executando comando: {command}")
            try:
                subprocess.run(command, shell=True, check=True)
                print("Comando executado com sucesso.  \n")
            except subprocess.CalledProcessError as e:
                print(f"Erro ao executar o comando: {e} \n")
                print(f"Saída de erro: {e.output.decode()}")

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
            #aqui exporta as variáveis de ambiente p trabalhar c os peers
            if org == 1:
                os.environ['CORE_PEER_LOCALMSPID'] = 'Org1MSP'
                os.environ['CORE_PEER_TLS_ROOTCERT_FILE'] = f'{os.getcwd()}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'
                os.environ['CORE_PEER_MSPCONFIGPATH'] = f'{os.getcwd()}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp'
                os.environ['CORE_PEER_ADDRESS'] = 'localhost:7051'
            elif org == 2:
                os.environ['CORE_PEER_LOCALMSPID'] = 'Org2MSP'
                os.environ['CORE_PEER_TLS_ROOTCERT_FILE'] = f'{os.getcwd()}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt'
                os.environ['CORE_PEER_MSPCONFIGPATH'] = f'{os.getcwd()}/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp'
                os.environ['CORE_PEER_ADDRESS'] = 'localhost:9051'

            os.environ['CORE_PEER_TLS_ENABLED'] = 'true'
            
            self.join_channel(org, channel_name, MAX_RETRY, CLI_DELAY)
            
            #self.set_anchor_peer(org, channel_name)


        return f"Channel '{channel_name}' created and joined"

    def join_channel(self, org, channel_name, max_retry, cli_delay):
        print('Executando Join Channel')
        ROOTDIR = os.getcwd()
        ORDERER_CA = f"{ROOTDIR}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt"
        

        blockfile = f"{ROOTDIR}/channel-artifacts/{channel_name}.block"
        peer_path = "/home/nobrega/Desktop/fabric-samples/bin/peer"

        env = os.environ.copy()
        env['FABRIC_CFG_PATH'] = f"{ROOTDIR}/configtx"

        print('Buscando o bloco de configuração do canal no orderer...')
        peer_cmd = [
            peer_path, "channel", "fetch", "0", blockfile,
            "-o", "localhost:7050",
            "--ordererTLSHostnameOverride", "mn.orderer",
            "-c", channel_name,
            "--tls", "--cafile", os.environ['CORE_PEER_TLS_ROOTCERT_FILE']
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
        def print_log(message):
            print("++++++++++++++++++++++++++++++++++++++++++++++++++")
            print(message)
            print("++++++++++++++++++++++++++++++++++++++++++++++++++")

        def fetch_channel_config(org, channel_name, output_file):
            print_log(f"Fetching channel config for channel {channel_name}")
            peer_cmd = [
                "/home/nobrega/Desktop/fabric-samples/bin/peer",
                "channel", "fetch", "config", output_file,
                "-o", "localhost:7050",
                "--ordererTLSHostnameOverride", "mn.orderer",
                "-c", channel_name,
                "--tls", "--cafile", f"{os.getcwd()}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt"
            ]
            subprocess.run(peer_cmd, check=True)

        def create_anchor_peer_update(org, channel_name):
            msp_id = f"Org{org}MSP"
            fetch_channel_config(org, channel_name, f"channel-artifacts/{msp_id}config.json")

            print_log(f"Generating anchor peer update transaction for Org{org} on channel {channel_name}")
            host = f"peer0.org{org}.example.com"
            port = 7051 + (org - 1) * 2000  # Calcula a porta baseada na organização

            with open(f"channel-artifacts/{msp_id}config.json", 'r') as f:
                config_json = json.load(f)

            anchor_peers = {
                "mod_policy": "Admins",
                "value": {
                    "anchor_peers": [{"host": host, "port": port}]
                },
                "version": "0"
            }

            config_json['channel_group']['groups']['Application']['groups'][msp_id]['values']['AnchorPeers'] = anchor_peers

            with open(f"channel-artifacts/{msp_id}modified_config.json", 'w') as f:
                json.dump(config_json, f, indent=4)

        def create_config_update(channel_name, msp_id):
            configtxlator_path = "/home/nobrega/Desktop/fabric-samples/bin/configtxlator"

            original = f"channel-artifacts/{msp_id}config.json"
            modified = f"channel-artifacts/{msp_id}modified_config.json"
            output = f"channel-artifacts/{msp_id}anchors.tx"

            def json_to_proto(json_file, proto_file):
                cmd = [configtxlator_path, "proto_encode", "--input", json_file, "--type", "common.Config"]
                with open(proto_file, 'wb') as f:
                    subprocess.run(cmd, check=True, stdout=f)

            original_proto = original.replace(".json", ".pb")
            modified_proto = modified.replace(".json", ".pb")

            # Converte JSON para Protobuf
            json_to_proto(original, original_proto)
            json_to_proto(modified, modified_proto)

            # Computa a atualização
            cmd = [
                configtxlator_path, "compute_update",
                "--channel_id", channel_name,
                "--original", original_proto,
                "--updated", modified_proto
            ]
            with open(output.replace(".tx", ".json"), 'w') as f:
                subprocess.run(cmd, check=True, stdout=f)

            # Converte a atualização para Protobuf
            cmd = [configtxlator_path, "proto_encode", "--input", output.replace(".tx", ".json"), "--type", "common.ConfigUpdate"]
            with open(output, 'wb') as f:
                subprocess.run(cmd, check=True, stdout=f)

        def update_anchor_peer(msp_id):
            print_log(f"Updating anchor peer for Org{org} on channel {channel_name}")
            peer_cmd = [
                "/home/nobrega/Desktop/fabric-samples/bin/peer", "channel", "update",
                "-o", "localhost:7050",
                "--ordererTLSHostnameOverride", "mn.orderer",
                "-c", channel_name,
                "-f", f"channel-artifacts/{msp_id}anchors.tx",
                "--tls", "--cafile", f"{os.getcwd()}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt"
            ]
            subprocess.run(peer_cmd, check=True)
            print_log(f"Anchor peer set for org '{msp_id}' on channel '{channel_name}'")

        msp_id = f"Org{org}MSP"
        create_anchor_peer_update(org, channel_name)
        create_config_update(channel_name, msp_id)
        update_anchor_peer(msp_id)