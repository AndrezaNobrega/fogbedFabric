from fogbed import Container
import os
from subprocess import check_output, CalledProcessError

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
            dcmd= 'orderer start',

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
            dcmd= 'peer node start',

        )
        self.exp.add_docker(container, org_instance)
        self.containers[name] = container
        return container

    def create_channel(self, channel_name):
        # Ensure necessary directories exist
        os.makedirs("channel-artifacts", exist_ok=True)

        # Set fixed parameters
        CLI_DELAY = "3"
        MAX_RETRY = "5"
        VERBOSE = "true"

        # Path to the configtxgen binary
        configtxgen_path = "/home/nobrega/Desktop/fabric-samples/bin/configtxgen"

        # Ensure the configtxgen binary is executable
        if not os.path.isfile(configtxgen_path) or not os.access(configtxgen_path, os.X_OK):
            raise Exception(f"Configtxgen binary not found or not executable at {configtxgen_path}")

        # Generate channel genesis block
        configtx_path = "/home/nobrega/Desktop/fabric-test/fabric-samples/test-network/configtx/configtx.yaml"
        profile = "ChannelUsingRaft"

        env = os.environ.copy()
        env['FABRIC_CFG_PATH'] = os.path.dirname(configtx_path)

        genesis_block_cmd = [
            configtxgen_path,
            "-profile", profile,
            "-outputBlock", f"./channel-artifacts/{channel_name}.block",
            "-channelID", channel_name
        ]

        try:
            print(f"Running command: {' '.join(genesis_block_cmd)}")
            output = check_output(genesis_block_cmd, env=env)
            print(f"Channel genesis block '{channel_name}.block' generated successfully.")
            print(output.decode())
        except CalledProcessError as e:
            print(f"Error output: {e.output.decode()}")
            raise Exception(f"Failed to generate channel configuration transaction: {e.output.decode()}")

        # Orderer variables
        ROOTDIR = os.getcwd()
        ORDERER_ADMIN_TLS_SIGN_CERT = f"{ROOTDIR}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt"
        ORDERER_ADMIN_TLS_PRIVATE_KEY = f"{ROOTDIR}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.key"
        ORDERER_CA = f"{ROOTDIR}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt"

        # Ensure the TLS files are accessible
        if not all(os.path.isfile(f) for f in [ORDERER_ADMIN_TLS_SIGN_CERT, ORDERER_ADMIN_TLS_PRIVATE_KEY, ORDERER_CA]):
            raise Exception("One or more TLS files are missing or not accessible")


        # Path to the osnadmin binary
        osnadmin_path = "/home/nobrega/Desktop/fabric-samples/bin/osnadmin"
        # Join the channel
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
            print(f"Channel '{channel_name}' created successfully.")
            print(output.decode())
        except CalledProcessError as e:
            print(f"Error output: {e.output.decode()}")
            raise Exception(f"Channel creation failed: {e.output.decode()}")

        # Join peers to channel and set anchor peers
        for org in [1, 2]:
            join_cmd = ["./scripts/joinChannel.sh", str(org)]
            try:
                print(f"Running command: {' '.join(join_cmd)}")
                output = check_output(join_cmd, env=env)
                print(f"Peer0.org{org} joined channel '{channel_name}' successfully.")
                print(output.decode())
            except CalledProcessError as e:
                print(f"Error output: {e.output.decode()}")
                raise Exception(f"Peer0.org{org} failed to join channel '{channel_name}': {e.output.decode()}")

            set_anchor_peer_cmd = ["./scripts/setAnchorPeer.sh", str(org), channel_name]
            try:
                print(f"Running command: {' '.join(set_anchor_peer_cmd)}")
                output = check_output(set_anchor_peer_cmd, env=env)
                print(f"Anchor peer for org{org} set successfully.")
                print(output.decode())
            except CalledProcessError as e:
                print(f"Error output: {e.output.decode()}")
                raise Exception(f"Failed to set anchor peer for org{org}: {e.output.decode()}")

        return f"Channel '{channel_name}' created and joined"

